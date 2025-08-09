#!/usr/bin/env python3
"""
Hybrid AI Assistant - General Purpose + Healthcare Billing Expert
Enhanced with Emotional UI and Voice Input
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
    current_sentiment: str = "neutral"
    sentiment_history: List[str] = field(default_factory=list)

class SentimentType(Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"
    ANXIOUS = "anxious"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    CONFUSED = "confused"

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

# ============= Sentiment Analysis =============

class SentimentAnalyzer:
    def __init__(self):
        self.positive_words = ['great', 'awesome', 'excellent', 'fantastic', 'wonderful', 'amazing', 'perfect', 'love', 'happy', 'excited', 'thank', 'thanks', 'good', 'nice', 'brilliant', 'outstanding']
        self.negative_words = ['terrible', 'awful', 'horrible', 'bad', 'worst', 'hate', 'frustrated', 'angry', 'sad', 'disappointed', 'upset', 'confused', 'difficult', 'problem', 'issue', 'error', 'wrong']
        self.anxious_words = ['worried', 'concerned', 'nervous', 'anxious', 'scared', 'afraid', 'stress', 'panic', 'uncertain', 'unsure']
        self.excited_words = ['excited', 'thrilled', 'amazing', 'wow', 'incredible', 'fantastic', 'brilliant', 'awesome']
        
    def analyze_sentiment(self, text: str) -> SentimentType:
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        anxious_count = sum(1 for word in self.anxious_words if word in text_lower)
        excited_count = sum(1 for word in self.excited_words if word in text_lower)
        
        # Check for question marks (confusion indicator)
        question_marks = text.count('?')
        exclamation_marks = text.count('!')
        
        # Determine sentiment
        if excited_count > 0 or exclamation_marks > 1:
            return SentimentType.EXCITED
        elif anxious_count > 0:
            return SentimentType.ANXIOUS
        elif question_marks > 1 and negative_count > 0:
            return SentimentType.CONFUSED
        elif negative_count > positive_count and negative_count > 1:
            return SentimentType.VERY_NEGATIVE if negative_count > 2 else SentimentType.NEGATIVE
        elif positive_count > negative_count and positive_count > 1:
            return SentimentType.VERY_POSITIVE if positive_count > 2 else SentimentType.POSITIVE
        elif 'frustrated' in text_lower or 'frustrating' in text_lower:
            return SentimentType.FRUSTRATED
        else:
            return SentimentType.NEUTRAL

# ============= AI Assistant Class =============

class HybridAIAssistant:
    def __init__(self):
        self.api_key = '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'
        self.billing_db = BillingCodesDB()
        self.sentiment_analyzer = SentimentAnalyzer()
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
    
    def get_empathetic_response_prefix(self, sentiment: SentimentType) -> str:
        """Generate empathetic response based on sentiment"""
        prefixes = {
            SentimentType.VERY_POSITIVE: "I'm so glad to hear your enthusiasm! 🌟 ",
            SentimentType.POSITIVE: "That's wonderful! 😊 ",
            SentimentType.EXCITED: "I can feel your excitement! 🎉 ",
            SentimentType.ANXIOUS: "I understand this might be causing some concern. Let me help ease your worries. 🤗 ",
            SentimentType.FRUSTRATED: "I can sense your frustration, and I'm here to help make this easier for you. 💙 ",
            SentimentType.CONFUSED: "No worries, I'm here to clear things up for you! 🧠 ",
            SentimentType.NEGATIVE: "I hear that you're having some difficulties. Let me help you with that. 💚 ",
            SentimentType.VERY_NEGATIVE: "I'm really sorry you're going through this. I'm here to support you. ❤️ ",
            SentimentType.NEUTRAL: ""
        }
        return prefixes.get(sentiment, "")
    
    def get_general_response(self, message: str, billing_context: bool = False) -> str:
        """Get response from OpenRouter API for general queries"""
        
        # Analyze sentiment
        sentiment = self.sentiment_analyzer.analyze_sentiment(message)
        self.context.current_sentiment = sentiment.value
        self.context.sentiment_history.append(sentiment.value)
        
        # Keep only last 10 sentiments
        if len(self.context.sentiment_history) > 10:
            self.context.sentiment_history = self.context.sentiment_history[-10:]
        
        # Prepare system prompt with empathy
        system_prompt = """You are a helpful, friendly, and empathetic AI assistant with expertise in healthcare billing codes. 
        You can assist with any topic - from casual conversation to complex questions. 
        When discussing medical billing codes, you provide accurate, detailed information.
        Be conversational, helpful, and engaging. Show empathy and understanding.
        Adapt your tone based on the user's emotional state - be more supportive if they seem frustrated or anxious."""
        
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
                
                # Add empathetic prefix based on sentiment
                empathy_prefix = self.get_empathetic_response_prefix(sentiment)
                if empathy_prefix:
                    ai_response = empathy_prefix + ai_response
                
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
        sentiment = self.sentiment_analyzer.analyze_sentiment(message)
        empathy_prefix = self.get_empathetic_response_prefix(sentiment)
        
        fallbacks = [
            "I'm having trouble connecting right now, but I'm still here to help! Could you rephrase your question?",
            "Let me think about that differently. What specific aspect would you like to know more about?",
            "That's an interesting question! While I process that, is there anything specific you'd like to explore?",
            "I'm here to help! Could you provide a bit more detail about what you're looking for?"
        ]
        return empathy_prefix + random.choice(fallbacks)
    
    def process_message(self, message: str) -> Tuple[str, str]:
        """Main method to process any message and return response with sentiment"""
        if not message.strip():
            return "Feel free to ask me anything! I can help with general questions or healthcare billing codes. 😊", "neutral"
        
        # Detect intent
        intent = self.detect_intent(message)
        
        # Route to appropriate handler
        if intent['is_billing'] and intent['codes_found']:
            response = self.handle_billing_query(message, intent['codes_found'])
        else:
            response = self.get_general_response(message, billing_context=intent['is_billing'])
        
        return response, self.context.current_sentiment
    
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
    
    # Process message and get sentiment
    response, sentiment = assistant.process_message(message)
    
    # Update UI based on sentiment (this will be handled by JavaScript)
    return response

def process_voice_input(audio):
    """Process voice input and return text"""
    if audio is None:
        return "No audio received. Please try again."
    
    # For now, return a placeholder message
    # In a real implementation, you'd use speech recognition here
    return "Voice input processed! (Speech recognition would be implemented here)"

def reset_chat():
    """Reset the conversation context"""
    assistant.reset_context()
    return []

# ============= Examples =============

examples = [
    "What is healthcare billing code A0429?",
    "Can you explain CPT code 99213 in detail?", 
    "Tell me about DRG 470",
    "I'm feeling frustrated with this billing issue",
    "This is confusing, can you help me understand?",
    "Thank you so much! This is exactly what I needed!",
    "How does artificial intelligence work?",
    "Give me a simple pasta recipe",
    "Write a short poem about nature"
]

# ============= Create Interface =============

def create_interface():
    """Create the Gradio ChatInterface with Emotional UI and Voice Input"""
    
    # Enhanced CSS with emotional UI and voice features
    custom_css = """
    /* Global Styles */
    .gradio-container {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif !important;
        max-width: 1200px !important;
        margin: auto !important;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
        min-height: 100vh !important;
        padding: 1rem !important;
        transition: all 0.5s ease !important;
    }
    
    /* Emotional UI Color Schemes */
    .sentiment-positive { background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%) !important; }
    .sentiment-very-positive { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%) !important; }
    .sentiment-negative { background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%) !important; }
    .sentiment-very-negative { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%) !important; }
    .sentiment-anxious { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%) !important; }
    .sentiment-frustrated { background: linear-gradient(135deg, #ff8a80 0%, #ffad80 100%) !important; }
    .sentiment-excited { background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%) !important; }
    .sentiment-confused { background: linear-gradient(135deg, #a8caba 0%, #5d4e75 100%) !important; }
    
    /* Enhanced Header with Mood Indicator */
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
        transition: all 0.5s ease;
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
    
    /* Mood Indicator */
    .mood-indicator {
        position: absolute;
        top: 1rem;
        right: 1rem;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        transition: all 0.5s ease;
        animation: breathe 3s ease-in-out infinite;
    }
    
    @keyframes breathe {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .mood-positive { background: rgba(132, 250, 176, 0.3) !important; }
    .mood-negative { background: rgba(255, 154, 158, 0.3) !important; }
    .mood-anxious { background: rgba(255, 236, 210, 0.3) !important; }
    .mood-excited { background: rgba(255, 216, 155, 0.3) !important; }
    
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
    
    /* Voice Input Button */
    .voice-btn {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 60px !important;
        height: 60px !important;
        font-size: 24px !important;
        margin: 0.5rem !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3) !important;
        position: relative;
        overflow: hidden;
    }
    
    .voice-btn:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.5) !important;
    }
    
    .voice-btn.recording {
        animation: recordPulse 1s ease-in-out infinite !important;
        background: linear-gradient(135deg, #ff3030 0%, #ff1010 100%) !important;
    }
    
    @keyframes recordPulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7); }
        70% { box-shadow: 0 0 0 20px rgba(255, 107, 107, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0); }
    }
    
    /* Chat Interface Styling with Emotional Feedback */
    .gradio-chatinterface {
        background: white !important;
        border-radius: 20px !important;
        box-shadow: 0 25px 50px rgba(0,0,0,0.15) !important;
        padding: 2rem !important;
        margin: 1rem 0 !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.5s ease !important;
    }
    
    .gradio-chatinterface.emotional-positive {
        border: 2px solid rgba(132, 250, 176, 0.5) !important;
        box-shadow: 0 25px 50px rgba(132, 250, 176, 0.2) !important;
    }
    
    .gradio-chatinterface.emotional-negative {
        border: 2px solid rgba(255, 154, 158, 0.5) !important;
        box-shadow: 0 25px 50px rgba(255, 154, 158, 0.2) !important;
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
    
    /* Empathy Animations */
    @keyframes empathyPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    @keyframes supportGlow {
        0%, 100% { box-shadow: 0 0 10px rgba(102, 126, 234, 0.3); }
        50% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.6); }
    }
    
    .empathy-support {
        animation: empathyPulse 2s ease-in-out infinite, supportGlow 3s ease-in-out infinite;
    }
    
    /* Voice Recognition Feedback */
    .voice-feedback {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: rgba(102, 126, 234, 0.9);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 50px;
        backdrop-filter: blur(10px);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
    }
    
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
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
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
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
        
        .mood-indicator {
            width: 50px;
            height: 50px;
            font-size: 20px;
        }
        
        .voice-btn {
            width: 50px !important;
            height: 50px !important;
            font-size: 20px !important;
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
    
    /* Sentiment-based message styling */
    .message-positive {
        border-left: 4px solid #84fab0 !important;
        background: linear-gradient(135deg, rgba(132, 250, 176, 0.1) 0%, rgba(143, 211, 244, 0.1) 100%) !important;
    }
    
    .message-negative {
        border-left: 4px solid #ff9a9e !important;
        background: linear-gradient(135deg, rgba(255, 154, 158, 0.1) 0%, rgba(254, 207, 239, 0.1) 100%) !important;
    }
    
    .message-anxious {
        border-left: 4px solid #ffecd2 !important;
        background: linear-gradient(135deg, rgba(255, 236, 210, 0.1) 0%, rgba(252, 182, 159, 0.1) 100%) !important;
    }
    """