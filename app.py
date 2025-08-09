#!/usr/bin/env python3
"""
Hybrid AI Assistant - General Purpose + Healthcare Billing Expert
A ChatGPT-style assistant using Gradio ChatInterface for simplicity
"""

import os
import sys
import json
import logging
import re
from typing import Dict, Optional, Tuple, List, Any, Iterator
from dataclasses import dataclass, field
from enum import Enum
import requests
import gradio as gr
from datetime import datetime
import random
import time

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
                    'max_tokens': 500,
                    'stream': False
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

# ============= Global Assistant Instance =============
assistant = HybridAIAssistant()

# ============= Chat Functions =============

def respond(message, history):
    """Response function for ChatInterface"""
    if not message.strip():
        return "Feel free to ask me anything! I can help with general questions or healthcare billing codes. 😊"
    
    # Process message
    response = assistant.process_message(message)
    return response

def reset_chat():
    """Reset the conversation context"""
    assistant.reset_context()
    return []

# ============= Examples =============

examples = [
    "What is healthcare billing code A0429?",
    "Can you explain CPT code 99213 in detail?",
    "Tell me about DRG 470",
    "How does artificial intelligence work?",
    "Give me a simple pasta recipe",
    "Teach me Python basics",
    "Write a short poem about nature",
    "Help me write a professional email template",
    "Give me creative story ideas"
]

# ============= Create Interface =============

def create_interface():
    """Create the Gradio ChatInterface"""
    
    # Enhanced CSS with modern design improvements
    custom_css = """
    /* Global Styles */
    .gradio-container {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif !important;
        max-width: 1200px !important;
        margin: auto !important;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
        min-height: 100vh !important;
        padding: 1rem !important;
    }
    
    /* Enhanced Header */
    .header-text {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .header-text::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.6; }
    }
    
    .header-text h1 {
        margin: 0;
        font-size: 3rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .header-text p {
        margin: 1rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.95;
        position: relative;
        z-index: 1;
        font-weight: 300;
    }
    
    .badge {
        background: rgba(255,255,255,0.25) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 0 5px rgba(255,255,255,0.3); }
        to { box-shadow: 0 0 20px rgba(255,255,255,0.6); }
    }
    
    /* Chat Interface Styling */
    .gradio-chatinterface {
        background: white !important;
        border-radius: 20px !important;
        box-shadow: 0 25px 50px rgba(0,0,0,0.15) !important;
        padding: 2rem !important;
        margin: 1rem 0 !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Enhanced Buttons */
    .reset-btn {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        margin: 0.5rem 0 !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3) !important;
    }
    
    .reset-btn:hover {
        background: linear-gradient(135deg, #ff5252 0%, #d32f2f 100%) !important;
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4) !important;
    }
    
    /* Example Buttons Enhancement */
    .gradio-chatinterface .examples .example {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 15px !important;
        padding: 0.75rem 1rem !important;
        margin: 0.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }
    
    .gradio-chatinterface .examples .example:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: #667eea !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Enhanced Stats Cards */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Enhanced Accordion */
    .gradio-accordion {
        background: rgba(255,255,255,0.9) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1) !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Feature Cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        color: #2d3748;
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .feature-desc {
        color: #64748b;
        line-height: 1.6;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 0.5rem !important;
        }
        
        .header-text h1 {
            font-size: 2rem;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .header-text {
            padding: 2rem 1rem;
        }
        
        .stats-container {
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }
        
        .stat-card {
            padding: 1.5rem;
        }
        
        .feature-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
    }
    
    /* Loading Animation */
    @keyframes shimmer {
        0% { background-position: -468px 0; }
        100% { background-position: 468px 0; }
    }
    
    .loading {
        animation: shimmer 1.5s ease-in-out infinite;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 400% 100%;
    }
    """
    
    with gr.Blocks(css=custom_css, title="AI Assistant + Healthcare Billing Expert") as demo:
        # Header
        gr.HTML("""
            <div class="header-text">
                <h1>🤖 AI Assistant <span style="font-size: 0.6em; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 16px;">PLUS</span></h1>
                <p>Your intelligent companion for any question + Healthcare Billing Expert</p>
            </div>
        """)
        
        # Main Chat Interface
        chat_interface = gr.ChatInterface(
            fn=respond,
            examples=examples,
            cache_examples=False
        )
        
        # Additional controls
        with gr.Row():
            with gr.Column(scale=1):
                reset_context_btn = gr.Button("🔄 Reset Context", elem_classes="reset-btn", size="sm")
            with gr.Column(scale=3):
                gr.HTML("")  # Spacer
            with gr.Column(scale=1):
                gr.HTML("""
                    <div style='text-align: right; color: #718096; font-size: 12px; margin-top: 0.5rem;'>
                        Powered by GPT-3.5 Turbo<br>
                        Healthcare Billing Database
                    </div>
                """)
        
        # Info section
        with gr.Accordion("ℹ️ About This Assistant", open=False):
            gr.HTML("""
                <div style="padding: 1rem; background: #f7fafc; border-radius: 8px; margin: 0.5rem 0;">
                    <h4 style="color: #2d3748; margin-top: 0;">🏥 Healthcare Billing Expert</h4>
                    <p style="color: #4a5568; margin-bottom: 1rem;">I'm specialized in healthcare billing codes including:</p>
                    <ul style="color: #4a5568; margin: 0.5rem 0;">
                        <li><strong>CPT Codes</strong> - Current Procedural Terminology</li>
                        <li><strong>HCPCS</strong> - Healthcare Common Procedure Coding System</li>
                        <li><strong>ICD-10</strong> - International Classification of Diseases</li>
                        <li><strong>DRG</strong> - Diagnosis-Related Groups</li>
                    </ul>
                    
                    <h4 style="color: #2d3748;">💬 General AI Assistant</h4>
                    <p style="color: #4a5568; margin: 0;">I can also help with general questions, writing, coding, learning, and creative tasks!</p>
                </div>
            """)
        
        # Connect reset button
        reset_context_btn.click(
            fn=reset_chat,
            outputs=chat_interface.chatbot
        )
    
    return demo

# ============= Launch =============

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )