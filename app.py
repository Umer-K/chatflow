#!/usr/bin/env python3
"""
Hybrid AI Assistant - ChatGPT Style Full Screen Interface
A full-screen ChatGPT clone with healthcare billing expertise
"""

import os
import sys
import json
import logging
import re
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field
from enum import Enum
import requests
import gradio as gr
from datetime import datetime
import random

# Set up environment
os.environ['OPENROUTER_API_KEY'] = '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'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= Data Classes =============

@dataclass
class CodeInfo:
    code: str
    description: str
    code_type: str
    additional_info: Optional[str] = None
    category: Optional[str] = None

@dataclass
class ConversationContext:
    messages: List[Dict[str, str]] = field(default_factory=list)
    detected_codes: List[str] = field(default_factory=list)
    last_topic: Optional[str] = None
    chat_history: List[Dict] = field(default_factory=list)
    current_chat_id: str = "chat_1"

# ============= Healthcare Billing Database =============

class BillingCodesDB:
    def __init__(self):
        self.codes = {
            'A0429': CodeInfo(
                code='A0429',
                description='Ambulance service, basic life support, emergency transport (BLS-emergency)',
                code_type='HCPCS',
                additional_info='Ground ambulance emergency transport with BLS level care. Used for emergency situations requiring immediate medical transport.',
                category='Ambulance Services'
            ),
            'A0428': CodeInfo(
                code='A0428',
                description='Ambulance service, basic life support, non-emergency transport',
                code_type='HCPCS',
                additional_info='Scheduled or non-urgent medical transport with basic life support.',
                category='Ambulance Services'
            ),
            '99213': CodeInfo(
                code='99213',
                description='Office visit for established patient, low complexity',
                code_type='CPT',
                additional_info='Typically 20-29 minutes. For straightforward medical issues.',
                category='E&M Services'
            ),
            '99214': CodeInfo(
                code='99214',
                description='Office visit for established patient, moderate complexity',
                code_type='CPT',
                additional_info='Typically 30-39 minutes. For moderately complex medical issues.',
                category='E&M Services'
            ),
            '99215': CodeInfo(
                code='99215',
                description='Office visit for established patient, high complexity',
                code_type='CPT',
                additional_info='Typically 40-54 minutes. For complex medical decision making.',
                category='E&M Services'
            ),
            '93000': CodeInfo(
                code='93000',
                description='Electrocardiogram (ECG/EKG) with interpretation',
                code_type='CPT',
                additional_info='Complete 12-lead ECG including test, interpretation, and report.',
                category='Cardiovascular'
            ),
            'DRG470': CodeInfo(
                code='DRG470',
                description='Major hip and knee joint replacement without complications',
                code_type='DRG',
                additional_info='Medicare payment group for joint replacement surgeries.',
                category='Orthopedic'
            ),
            'Z79.899': CodeInfo(
                code='Z79.899',
                description='Other long term drug therapy',
                code_type='ICD-10',
                additional_info='Indicates patient is on long-term medication.',
                category='Diagnosis'
            ),
            'E1399': CodeInfo(
                code='E1399',
                description='Durable medical equipment, miscellaneous',
                code_type='HCPCS',
                additional_info='For DME not elsewhere classified.',
                category='Equipment'
            ),
            'J3420': CodeInfo(
                code='J3420',
                description='Vitamin B-12 injection',
                code_type='HCPCS',
                additional_info='Cyanocobalamin up to 1000 mcg.',
                category='Injections'
            )
        }
    
    def lookup(self, code: str) -> Optional[CodeInfo]:
        code = code.strip().upper()
        if code in self.codes:
            return self.codes[code]
        if code.isdigit() and len(code) == 3:
            drg_code = f"DRG{code}"
            if drg_code in self.codes:
                return self.codes[drg_code]
        return None
    
    def search_codes(self, text: str) -> List[str]:
        """Extract potential billing codes from text"""
        found_codes = []
        patterns = [
            r'\b([A-V][0-9]{4})\b',  # HCPCS
            r'\b([0-9]{5})\b',  # CPT
            r'\bDRG\s*([0-9]{3})\b',  # DRG
            r'\b([A-Z][0-9]{2}\.?[0-9]{0,3})\b',  # ICD-10
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.upper())
            for match in matches:
                if self.lookup(match):
                    found_codes.append(match)
        
        return found_codes

# ============= AI Assistant Class =============

class HybridAIAssistant:
    def __init__(self):
        self.api_key = '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'
        self.billing_db = BillingCodesDB()
        self.context = ConversationContext()
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://huggingface.co',
            'X-Title': 'Hybrid AI Assistant'
        }
    
    def detect_intent(self, message: str) -> Dict[str, Any]:
        """Detect if the message is about billing codes or general conversation"""
        lower_msg = message.lower()
        codes = self.billing_db.search_codes(message)
        
        billing_keywords = ['code', 'cpt', 'hcpcs', 'icd', 'drg', 'billing', 'medical code']
        is_billing = any(keyword in lower_msg for keyword in billing_keywords) or len(codes) > 0
        
        return {
            'is_billing': is_billing,
            'codes_found': codes,
            'message': message
        }
    
    def handle_billing_query(self, message: str, codes: List[str]) -> str:
        """Handle healthcare billing specific queries"""
        responses = []
        
        if codes:
            for code in codes[:3]:
                info = self.billing_db.lookup(code)
                if info:
                    response = f"### {info.code} ({info.code_type})\n\n"
                    response += f"**Description:** {info.description}\n\n"
                    if info.additional_info:
                        response += f"**Details:** {info.additional_info}\n\n"
                    if info.category:
                        response += f"**Category:** {info.category}\n"
                    responses.append(response)
        
        if responses:
            final_response = "I found information about the billing code(s) you mentioned:\n\n"
            final_response += "\n---\n\n".join(responses)
            final_response += "\n\n💡 Need more details? Feel free to ask specific questions about these codes!"
            return final_response
        else:
            return self.get_general_response(message, billing_context=True)
    
    def get_general_response(self, message: str, billing_context: bool = False) -> str:
        """Get response from OpenRouter API for general queries"""
        
        system_prompt = """You are a helpful, friendly AI assistant with expertise in healthcare billing codes. 
        You can assist with any topic - from casual conversation to complex questions. 
        When discussing medical billing codes, you provide accurate, detailed information.
        Be conversational, helpful, and engaging. Format your responses with markdown for better readability.
        Use headers (###), bold (**text**), and bullet points where appropriate."""
        
        if billing_context:
            system_prompt += "\nThe user is asking about medical billing. Provide helpful information even if you don't have specific code details."
        
        messages = [{'role': 'system', 'content': system_prompt}]
        
        for msg in self.context.messages[-10:]:
            messages.append(msg)
        
        messages.append({'role': 'user', 'content': message})
        
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=self.headers,
                json={
                    'model': 'openai/gpt-3.5-turbo',
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': 500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                self.context.messages.append({'role': 'user', 'content': message})
                self.context.messages.append({'role': 'assistant', 'content': ai_response})
                
                if len(self.context.messages) > 20:
                    self.context.messages = self.context.messages[-20:]
                
                return ai_response
            else:
                logger.error(f"API error: {response.status_code}")
                return self.get_fallback_response(message)
                
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return self.get_fallback_response(message)
    
    def get_fallback_response(self, message: str) -> str:
        """Fallback responses when API fails"""
        fallbacks = [
            "I'm having trouble connecting right now, but I'm still here to help! Could you rephrase your question?",
            "Let me think about that differently. What specific aspect would you like to know more about?",
            "That's an interesting question! While I process that, is there anything specific you'd like to explore?"
        ]
        return random.choice(fallbacks)
    
    def process_message(self, message: str) -> str:
        """Main method to process any message"""
        if not message.strip():
            return "Feel free to ask me anything! I can help with general questions or healthcare billing codes. 😊"
        
        intent = self.detect_intent(message)
        
        if intent['is_billing'] and intent['codes_found']:
            return self.handle_billing_query(message, intent['codes_found'])
        else:
            return self.get_general_response(message, billing_context=intent['is_billing'])
    
    def reset_context(self):
        """Reset conversation context"""
        self.context = ConversationContext()

# ============= Create ChatGPT-Style Interface =============

def create_interface():
    assistant = HybridAIAssistant()
    
    # Full-screen ChatGPT CSS
    custom_css = """
    /* Full screen layout */
    .gradio-container {
        margin: 0 !important;
        padding: 0 !important;
        width: 100vw !important;
        max-width: 100vw !important;
        height: 100vh !important;
        display: flex !important;
        flex-direction: column !important;
        font-family: 'Söhne', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        background: #f9f9f9 !important;
    }
    
    /* Remove all Gradio default spacing */
    .contain, .wrapper, .wrap, .block {
        border: none !important;
        background: transparent !important;
    }
    
    /* Main container layout */
    .main-container {
        display: flex;
        height: 100vh;
        width: 100vw;
        overflow: hidden;
        background: #fff;
    }
    
    /* Sidebar */
    .sidebar {
        width: 260px;
        background: #202123;
        color: white;
        padding: 0;
        display: flex;
        flex-direction: column;
        height: 100vh;
        overflow-y: auto;
    }
    
    .sidebar-header {
        padding: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .new-chat-btn {
        width: 100%;
        padding: 12px 16px;
        background: transparent;
        border: 1px solid rgba(255,255,255,0.2);
        color: white;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: background 0.2s;
    }
    
    .new-chat-btn:hover {
        background: rgba(255,255,255,0.1);
    }
    
    .chat-history {
        flex: 1;
        padding: 8px;
        overflow-y: auto;
    }
    
    .chat-item {
        padding: 12px 16px;
        margin: 2px 0;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
        color: rgba(255,255,255,0.8);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: background 0.2s;
    }
    
    .chat-item:hover {
        background: rgba(255,255,255,0.05);
    }
    
    .chat-item.active {
        background: rgba(255,255,255,0.1);
        color: white;
    }
    
    /* Main chat area */
    .chat-container {
        flex: 1;
        display: flex;
        flex-direction: column;
        background: #fff;
        position: relative;
    }
    
    /* Chat messages area */
    #chatbot {
        flex: 1;
        overflow-y: auto;
        padding: 0;
        background: #fff;
        display: flex;
        flex-direction: column;
    }
    
    #chatbot > .wrap {
        max-width: 48rem;
        margin: 0 auto;
        width: 100%;
        padding: 2rem 1rem;
    }
    
    /* Message styling */
    .message {
        padding: 1.5rem 0;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .message.user {
        background: #fff;
    }
    
    .message.assistant {
        background: #f7f7f8;
    }
    
    .message-content {
        max-width: 48rem;
        margin: 0 auto;
        display: flex;
        gap: 1.5rem;
        padding: 0 1rem;
    }
    
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 4px;
        background: #5436DA;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 14px;
        flex-shrink: 0;
    }
    
    .avatar.assistant {
        background: #19c37d;
    }
    
    .message-text {
        flex: 1;
        line-height: 1.6;
        font-size: 15px;
        color: #2d2d2d;
    }
    
    .message-text h1 { font-size: 1.8em; margin: 1em 0 0.5em; }
    .message-text h2 { font-size: 1.5em; margin: 1em 0 0.5em; }
    .message-text h3 { font-size: 1.2em; margin: 1em 0 0.5em; font-weight: 600; }
    .message-text p { margin: 0.8em 0; }
    .message-text ul, .message-text ol { margin: 0.8em 0; padding-left: 1.5em; }
    .message-text li { margin: 0.4em 0; }
    .message-text code { 
        background: #f3f4f6; 
        padding: 2px 6px; 
        border-radius: 4px; 
        font-family: 'Consolas', monospace;
        font-size: 0.9em;
    }
    .message-text pre {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1em;
        border-radius: 6px;
        overflow-x: auto;
        margin: 1em 0;
    }
    .message-text strong { font-weight: 600; }
    
    /* Input area */
    .input-container {
        border-top: 1px solid #e5e5e5;
        background: #fff;
        padding: 1rem 0;
    }
    
    .input-wrapper {
        max-width: 48rem;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    #input-box {
        width: 100%;
        border: 1px solid #d9d9e3;
        border-radius: 12px;
        padding: 12px 48px 12px 16px;
        font-size: 15px;
        resize: none;
        background: #fff;
        color: #2d2d2d;
        outline: none;
        box-shadow: 0 0 0 2px transparent;
        transition: all 0.2s;
    }
    
    #input-box:focus {
        border-color: #10a37f;
        box-shadow: 0 0 0 2px rgba(16,163,127,0.1);
    }
    
    .send-button {
        position: absolute;
        right: 12px;
        bottom: 12px;
        background: #10a37f;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 12px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: background 0.2s;
    }
    
    .send-button:hover {
        background: #0d8f6e;
    }
    
    .send-button:disabled {
        background: #e5e5e5;
        cursor: not-allowed;
    }
    
    /* Welcome screen */
    .welcome-screen {
        max-width: 48rem;
        margin: 0 auto;
        padding: 3rem 1rem;
        text-align: center;
    }
    
    .welcome-title {
        font-size: 2rem;
        font-weight: 600;
        color: #2d2d2d;
        margin-bottom: 1rem;
    }
    
    .welcome-subtitle {
        font-size: 1rem;
        color: #6e6e80;
        margin-bottom: 3rem;
    }
    
    .example-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-top: 2rem;
    }
    
    .example-card {
        background: #f7f7f8;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 16px;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
    }
    
    .example-card:hover {
        background: #ececf1;
        border-color: #d9d9e3;
    }
    
    .example-title {
        font-weight: 600;
        font-size: 14px;
        color: #2d2d2d;
        margin-bottom: 4px;
    }
    
    .example-text {
        font-size: 13px;
        color: #6e6e80;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .sidebar {
            display: none;
        }
        
        .input-wrapper {
            padding: 0 0.5rem;
        }
        
        #chatbot > .wrap {
            padding: 1rem 0.5rem;
        }
    }
    """
    
    with gr.Blocks(css=custom_css, theme=gr.themes.Base(), title="AI Assistant") as app:
        
        # Welcome message formatted with markdown
        welcome_html = """
<div class="welcome-screen">
    <h1 class="welcome-title">AI Assistant Plus</h1>
    <p class="welcome-subtitle">Your intelligent companion for any question + Healthcare Billing Expert</p>
    
    <div class="example-grid">
        <div class="example-card" onclick="document.querySelector('#input-box textarea').value='What is medical billing code A0429?'; document.querySelector('#input-box textarea').dispatchEvent(new Event('input'));">
            <div class="example-title">🏥 Medical Billing</div>
            <div class="example-text">"Explain code A0429"</div>
        </div>
        <div class="example-card" onclick="document.querySelector('#input-box textarea').value='How does machine learning work?'; document.querySelector('#input-box textarea').dispatchEvent(new Event('input'));">
            <div class="example-title">🤖 Learn</div>
            <div class="example-text">"Explain ML simply"</div>
        </div>
        <div class="example-card" onclick="document.querySelector('#input-box textarea').value='Write a professional email template'; document.querySelector('#input-box textarea').dispatchEvent(new Event('input'));">
            <div class="example-title">✍️ Write</div>
            <div class="example-text">"Draft an email"</div>
        </div>
        <div class="example-card" onclick="document.querySelector('#input-box textarea').value='Give me a healthy recipe idea'; document.querySelector('#input-box textarea').dispatchEvent(new Event('input'));">
            <div class="example-title">🍳 Create</div>
            <div class="example-text">"Recipe ideas"</div>
        </div>
    </div>
</div>
"""
        
        # Main layout with HTML structure
        gr.HTML("""
<div class="main-container">
    <!-- Sidebar -->
    <div class="sidebar">
        <div class="sidebar-header">
            <button class="new-chat-btn">
                <span>+</span>
                <span>New chat</span>
            </button>
        </div>
        <div class="chat-history">
            <div class="chat-item active">Healthcare Billing Expert</div>
            <div class="chat-item">General Assistant</div>
            <div class="chat-item">Previous Chat</div>
        </div>
    </div>
    
    <!-- Main chat area -->
    <div class="chat-container">
        """)
        
        # Chat interface
        chatbot_ui = gr.Chatbot(
            value=[],
            elem_id="chatbot",
            show_label=False,
            type="messages",
            height=600,
            render_markdown=True,
            avatar_images=None
        )
        
        # Set initial welcome message
        chatbot_ui.value = [
            {
                "role": "assistant",
                "content": welcome_html
            }
        ]
        
        # Input area
        with gr.Row(elem_classes="input-container"):
            with gr.Column(elem_classes="input-wrapper"):
                msg = gr.Textbox(
                    placeholder="Message AI Assistant...",
                    show_label=False,
                    elem_id="input-box",
                    lines=1,
                    max_lines=5,
                    autofocus=True
                )
        
        gr.HTML("</div></div>")
        
        # Event handlers
        def respond(message, chat_history):
            if not message.strip():
                return "", chat_history
            
            # Process message
            response = assistant.process_message(message)
            
            # Update chat history
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": response})
            
            return "", chat_history
        
        # Connect events
        msg.submit(respond, [msg, chatbot_ui], [msg, chatbot_ui])
    
    return app

# Launch
if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        favicon_path=None
    )