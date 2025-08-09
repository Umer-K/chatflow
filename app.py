#!/usr/bin/env python3
"""
Hybrid AI Assistant - General Purpose + Healthcare Billing Expert
A ChatGPT-style assistant that can handle any conversation while specializing in healthcare billing codes
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
            ),
            '80053': CodeInfo(
                code='80053',
                description='Comprehensive metabolic panel',
                code_type='CPT',
                additional_info='14 blood tests including glucose, kidney, and liver function.',
                category='Laboratory'
            ),
            '70450': CodeInfo(
                code='70450',
                description='CT head/brain without contrast',
                code_type='CPT',
                additional_info='Computed tomography of head without contrast material.',
                category='Radiology'
            ),
            '90837': CodeInfo(
                code='90837',
                description='Psychotherapy, 60 minutes',
                code_type='CPT',
                additional_info='Individual psychotherapy session.',
                category='Mental Health'
            ),
            '36415': CodeInfo(
                code='36415',
                description='Venipuncture (blood draw)',
                code_type='CPT',
                additional_info='Collection of blood by needle.',
                category='Laboratory'
            ),
            '99282': CodeInfo(
                code='99282',
                description='Emergency department visit, low-moderate severity',
                code_type='CPT',
                additional_info='ED visit for problems of low to moderate severity.',
                category='Emergency'
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
        
        # Check for billing codes in the message
        codes = self.billing_db.search_codes(message)
        
        # Keywords that suggest billing/medical coding questions
        billing_keywords = ['code', 'cpt', 'hcpcs', 'icd', 'drg', 'billing', 'medical code', 
                          'healthcare code', 'diagnosis code', 'procedure code']
        
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
            for code in codes[:3]:  # Limit to first 3 codes
                info = self.billing_db.lookup(code)
                if info:
                    response = f"**{info.code} ({info.code_type})**\n"
                    response += f"📋 **Description:** {info.description}\n"
                    if info.additional_info:
                        response += f"ℹ️ **Details:** {info.additional_info}\n"
                    if info.category:
                        response += f"🏷️ **Category:** {info.category}\n"
                    responses.append(response)
        
        if responses:
            final_response = "I found information about the billing code(s) you mentioned:\n\n"
            final_response += "\n---\n".join(responses)
            final_response += "\n\n💡 **Need more details?** Feel free to ask specific questions about these codes!"
            return final_response
        else:
            return self.get_general_response(message, billing_context=True)
    
    def get_general_response(self, message: str, billing_context: bool = False) -> str:
        """Get response from OpenRouter API for general queries"""
        
        # Prepare system prompt
        system_prompt = """You are a helpful, friendly AI assistant with expertise in healthcare billing codes. 
        You can assist with any topic - from casual conversation to complex questions. 
        When discussing medical billing codes, you provide accurate, detailed information.
        Be conversational, helpful, and engaging. Use emojis occasionally to be friendly.
        Keep responses concise but informative."""
        
        if billing_context:
            system_prompt += "\nThe user is asking about medical billing. Provide helpful information even if you don't have specific code details."
        
        # Build conversation history for context
        messages = [{'role': 'system', 'content': system_prompt}]
        
        # Add recent conversation history (last 5 exchanges)
        for msg in self.context.messages[-10:]:
            messages.append(msg)
        
        # Add current message
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
                
                # Update context
                self.context.messages.append({'role': 'user', 'content': message})
                self.context.messages.append({'role': 'assistant', 'content': ai_response})
                
                # Keep only last 20 messages in context
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
            "That's an interesting question! While I process that, is there anything specific you'd like to explore?",
            "I'm here to help! Could you provide a bit more detail about what you're looking for?"
        ]
        return random.choice(fallbacks)
    
    def process_message(self, message: str) -> str:
        """Main method to process any message"""
        if not message.strip():
            return "Feel free to ask me anything! I can help with general questions or healthcare billing codes. 😊"
        
        # Detect intent
        intent = self.detect_intent(message)
        
        # Route to appropriate handler
        if intent['is_billing'] and intent['codes_found']:
            return self.handle_billing_query(message, intent['codes_found'])
        else:
            return self.get_general_response(message, billing_context=intent['is_billing'])
    
    def reset_context(self):
        """Reset conversation context"""
        self.context = ConversationContext()

# ============= Gradio Interface =============

def create_interface():
    assistant = HybridAIAssistant()
    
    # ChatGPT-style CSS
    custom_css = """
    /* Main container */
    .gradio-container {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif !important;
        max-width: 900px !important;
        margin: auto !important;
        background: #ffffff !important;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px 15px 0 0;
        margin-bottom: 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .header-title {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1rem;
        margin-top: 0.5rem;
        text-align: center;
    }
    
    /* Chat container */
    #chatbot {
        height: 500px !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
        background: #ffffff !important;
    }
    
    /* Message styling */
    .message {
        padding: 1rem !important;
        margin: 0.5rem !important;
        border-radius: 12px !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }
    
    .user-message {
        background: #f3f4f6 !important;
        border: 1px solid #e5e7eb !important;
        margin-left: 20% !important;
    }
    
    .bot-message {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        margin-right: 20% !important;
    }
    
    /* Input area */
    #input-box {
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 14px 16px !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
        background: #ffffff !important;
    }
    
    #input-box:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none !important;
    }
    
    /* Buttons */
    .primary-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        cursor: pointer !important;
        transition: transform 0.2s ease !important;
    }
    
    .primary-btn:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    }
    
    .secondary-btn {
        background: #f3f4f6 !important;
        color: #374151 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    .secondary-btn:hover {
        background: #e5e7eb !important;
        border-color: #d1d5db !important;
    }
    
    /* Example chips */
    .example-chip {
        display: inline-block !important;
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 20px !important;
        padding: 8px 16px !important;
        margin: 4px !important;
        font-size: 14px !important;
        color: #4b5563 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    .example-chip:hover {
        background: #f9fafb !important;
        border-color: #667eea !important;
        color: #667eea !important;
        transform: translateY(-1px) !important;
    }
    
    /* Info cards */
    .info-card {
        background: linear-gradient(135deg, #f6f8fb 0%, #f1f5f9 100%);
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 0 !important;
        }
        
        .header-title {
            font-size: 1.5rem;
        }
        
        .user-message, .bot-message {
            margin-left: 5% !important;
            margin-right: 5% !important;
        }
    }
    """
    
    with gr.Blocks(css=custom_css, theme=gr.themes.Base()) as app:
        # Header
        gr.HTML("""
            <div class="header-container">
                <h1 class="header-title">
                    <span>🤖</span>
                    <span>AI Assistant</span>
                    <span style="font-size: 0.8em; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 12px;">PLUS</span>
                </h1>
                <p class="header-subtitle">Your intelligent companion for any question + Healthcare Billing Expert</p>
            </div>
        """)
        
        # Main chat interface
        chatbot_ui = gr.Chatbot(
            value=[[None, "👋 **Hello! I'm your AI Assistant!**\n\nI can help you with:\n\n🏥 **Healthcare Billing Codes** - I'm an expert in CPT, HCPCS, ICD-10, and DRG codes\n💬 **General Conversation** - Ask me anything!\n📚 **Learning & Education** - Help with various topics\n✍️ **Writing & Creation** - Stories, emails, ideas\n🔧 **Problem Solving** - Let's work through challenges together\n\n**Try asking:**\n• 'What is billing code A0429?'\n• 'Help me write an email'\n• 'Explain quantum physics simply'\n• 'What's the weather like?'\n\nHow can I assist you today? 😊"]],
            elem_id="chatbot",
            show_label=False,
            type="messages",
            bubble_full_width=False,
            height=500
        )
        
        # Input section
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Ask me anything... (e.g., 'Explain code 99213' or 'Help me write a story')",
                show_label=False,
                elem_id="input-box",
                scale=5,
                lines=1,
                max_lines=5
            )
            send_btn = gr.Button("Send", elem_classes="primary-btn", scale=1)
        
        # Quick examples
        gr.HTML("<div style='text-align: center; margin: 1rem 0; color: #6b7280; font-size: 14px;'>Quick Examples</div>")
        
        with gr.Row():
            ex_col1 = gr.Column(scale=1)
            ex_col2 = gr.Column(scale=1)
            ex_col3 = gr.Column(scale=1)
        
        with ex_col1:
            gr.HTML("<div style='color: #667eea; font-weight: 600; font-size: 13px; margin-bottom: 8px;'>🏥 Medical Billing</div>")
            ex1 = gr.Button("What is code A0429?", elem_classes="example-chip", size="sm")
            ex2 = gr.Button("Explain CPT 99213", elem_classes="example-chip", size="sm")
            ex3 = gr.Button("DRG 470 details", elem_classes="example-chip", size="sm")
        
        with ex_col2:
            gr.HTML("<div style='color: #667eea; font-weight: 600; font-size: 13px; margin-bottom: 8px;'>💭 General Questions</div>")
            ex4 = gr.Button("How does AI work?", elem_classes="example-chip", size="sm")
            ex5 = gr.Button("Recipe for pasta", elem_classes="example-chip", size="sm")
            ex6 = gr.Button("Python tutorial", elem_classes="example-chip", size="sm")
        
        with ex_col3:
            gr.HTML("<div style='color: #667eea; font-weight: 600; font-size: 13px; margin-bottom: 8px;'>✍️ Creative Help</div>")
            ex7 = gr.Button("Write a poem", elem_classes="example-chip", size="sm")
            ex8 = gr.Button("Email template", elem_classes="example-chip", size="sm")
            ex9 = gr.Button("Story ideas", elem_classes="example-chip", size="sm")
        
        # Control buttons
        with gr.Row():
            clear_btn = gr.Button("🔄 New Chat", elem_classes="secondary-btn", size="sm")
            gr.HTML("<div style='flex-grow: 1;'></div>")
            gr.HTML("""
                <div style='text-align: right; color: #6b7280; font-size: 12px;'>
                    Powered by GPT-3.5 • Healthcare Billing Database
                </div>
            """)
        
        # Footer info
        gr.HTML("""
            <div class="info-card" style="margin-top: 2rem;">
                <div style="display: flex; justify-content: space-around; text-align: center;">
                    <div>
                        <div style="color: #667eea; font-size: 24px; font-weight: bold;">15+</div>
                        <div style="color: #6b7280; font-size: 12px;">Medical Codes</div>
                    </div>
                    <div>
                        <div style="color: #667eea; font-size: 24px; font-weight: bold;">∞</div>
                        <div style="color: #6b7280; font-size: 12px;">Topics</div>
                    </div>
                    <div>
                        <div style="color: #667eea; font-size: 24px; font-weight: bold;">24/7</div>
                        <div style="color: #6b7280; font-size: 12px;">Available</div>
                    </div>
                    <div>
                        <div style="color: #667eea; font-size: 24px; font-weight: bold;">Fast</div>
                        <div style="color: #6b7280; font-size: 12px;">Responses</div>
                    </div>
                </div>
            </div>
        """)
        
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
        
        def clear_chat():
            assistant.reset_context()
            welcome = """👋 **Chat cleared! Ready for a new conversation.**

I'm here to help with anything you need - from healthcare billing codes to general questions!

What would you like to know? 😊"""
            return [[None, welcome]]
        
        # Connect events
        msg.submit(respond, [msg, chatbot_ui], [msg, chatbot_ui])
        send_btn.click(respond, [msg, chatbot_ui], [msg, chatbot_ui])
        clear_btn.click(clear_chat, outputs=[chatbot_ui])
        
        # Example button handlers
        ex1.click(lambda: "What is healthcare billing code A0429?", outputs=msg)
        ex2.click(lambda: "Can you explain CPT code 99213 in detail?", outputs=msg)
        ex3.click(lambda: "Tell me about DRG 470", outputs=msg)
        ex4.click(lambda: "How does artificial intelligence work?", outputs=msg)
        ex5.click(lambda: "Give me a simple pasta recipe", outputs=msg)
        ex6.click(lambda: "Teach me Python basics", outputs=msg)
        ex7.click(lambda: "Write a short poem about nature", outputs=msg)
        ex8.click(lambda: "Help me write a professional email template", outputs=msg)
        ex9.click(lambda: "Give me creative story ideas", outputs=msg)
    
    return app

# Launch
if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )