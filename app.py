#!/usr/bin/env python3
"""
Hybrid AI Assistant - General Purpose + Healthcare Billing Expert
Enhanced with Emotional UI and Voice Input - HUGGING FACE SPACES VERSION
"""

import os
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up environment - Hugging Face Spaces will handle API keys via secrets
API_KEY = os.getenv('OPENROUTER_API_KEY', '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')

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
        self.api_key = API_KEY
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

# ============= Chat Functions for Gradio =============

def chat_with_assistant(message, history):
    """Main chat function for Gradio ChatInterface"""
    try:
        if not message or not message.strip():
            return "Feel free to ask me anything! I can help with general questions or healthcare billing codes. 😊"
        
        # Process message and get response
        response, sentiment = assistant.process_message(message.strip())
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return "I apologize, but I encountered an error processing your message. Please try again!"

def quick_code_lookup(code):
    """Quick billing code lookup function"""
    try:
        if not code or not code.strip():
            return "Please enter a billing code to look up."
        
        info = assistant.billing_db.lookup(code.strip())
        if info:
            result = f"**{info.code} ({info.code_type})**\n\n"
            result += f"**Description:** {info.description}\n\n"
            if info.additional_info:
                result += f"**Details:** {info.additional_info}\n\n"
            if info.category:
                result += f"**Category:** {info.category}"
            return result
        else:
            return f"Code '{code.strip()}' not found in database. Try asking in the chat for more help!"
    except Exception as e:
        logger.error(f"Code lookup error: {e}")
        return "Error looking up code. Please try again."

def process_voice_input(audio_file):
    """Process voice input (placeholder for speech recognition)"""
    if audio_file is None:
        return "No audio received. Please try recording again."
    
    # Placeholder for speech recognition
    return "Voice input received! (Speech recognition would be implemented here with libraries like Whisper or SpeechRecognition)"

def reset_conversation():
    """Reset the conversation context"""
    try:
        assistant.reset_context()
        return "✅ Conversation reset successfully!", ""
    except Exception as e:
        logger.error(f"Reset error: {e}")
        return "Error resetting conversation.", ""

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

# ============= Custom CSS for Hugging Face Spaces =============
custom_css = """
/* Enhanced Hugging Face Spaces Compatible CSS */
.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    padding: 1rem !important;
}

/* Header Styling */
.header-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 1.5rem;
    text-align: center;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.header-banner h1 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.header-banner p {
    margin: 0.5rem 0 0 0;
    font-size: 1.1rem;
    opacity: 0.9;
}

/* Enhanced Buttons */
.custom-button {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.3s ease !important;
}

.custom-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4) !important;
}

/* Chat Interface */
.gradio-chatbot {
    border-radius: 15px !important;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1) !important;
    background: white !important;
}

/* Feature Cards */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.feature-card {
    background: rgba(255,255,255,0.95);
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
    text-align: center;
}

.feature-card:hover {
    transform: translateY(-5px);
}

.feature-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

/* Stats */
.stats-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.stat-item {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border-top: 3px solid #667eea;
}

.stat-number {
    font-size: 1.8rem;
    font-weight: bold;
    color: #667eea;
}

.stat-label {
    font-size: 0.8rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .header-banner h1 {
        font-size: 2rem;
    }
    
    .feature-grid {
        grid-template-columns: 1fr;
    }
    
    .stats-container {
        grid-template-columns: repeat(2, 1fr);
    }
}
"""

# ============= Main Gradio Interface =============

def create_gradio_interface():
    """Create the main Gradio interface optimized for Hugging Face Spaces"""
    
    with gr.Blocks(
        css=custom_css,
        title="🏥 Hybrid AI Assistant - Healthcare Billing Expert"
    ) as demo:
        
        # Header Section
        gr.HTML("""
        <div class="header-banner">
            <h1>🏥 Hybrid AI Assistant</h1>
            <p>Your intelligent companion for healthcare billing codes and general assistance</p>
            <div style="margin-top: 1rem;">
                <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0 0.25rem; font-size: 0.9rem;">💬 General AI</span>
                <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0 0.25rem; font-size: 0.9rem;">🏥 Medical Billing</span>
                <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0 0.25rem; font-size: 0.9rem;">🎭 Emotional AI</span>
                <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 15px; margin: 0 0.25rem; font-size: 0.9rem;">🎙️ Voice Ready</span>
            </div>
        </div>
        """)
        
        # Stats Section
        gr.HTML("""
        <div class="stats-container">
            <div class="stat-item">
                <div class="stat-number">15+</div>
                <div class="stat-label">Billing Codes</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">9</div>
                <div class="stat-label">Sentiment Types</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">24/7</div>
                <div class="stat-label">Available</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">∞</div>
                <div class="stat-label">Conversations</div>
            </div>
        </div>
        """)
        
        # Main Chat Interface
        chatbot = gr.ChatInterface(
            chat_with_assistant,
            examples=examples,
            title="",
            description="💬 Start chatting! I can help with healthcare billing codes, general questions, and adapt to your emotional tone."
        )
        
        # Additional Tools Section
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🏥 Quick Code Lookup")
                code_input = gr.Textbox(
                    label="Enter Billing Code",
                    placeholder="e.g., A0429, 99213, DRG470...",
                    lines=1
                )
                lookup_btn = gr.Button("🔍 Look Up Code", elem_classes=["custom-button"])
                code_output = gr.Textbox(
                    label="Code Information",
                    placeholder="Code details will appear here...",
                    lines=6,
                    interactive=False
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 🎙️ Voice Input")
                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="Voice Input"
                )
                voice_btn = gr.Button("🎤 Process Voice", elem_classes=["custom-button"])
                voice_output = gr.Textbox(
                    label="Voice Processing Result",
                    placeholder="Voice processing result will appear here...",
                    lines=3,
                    interactive=False
                )
        
        # Features Section
        gr.HTML("""
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <h3>Smart AI Assistant</h3>
                <p>Advanced AI that understands context and provides intelligent responses.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🏥</div>
                <h3>Healthcare Billing Expert</h3>
                <p>Comprehensive database of CPT, HCPCS, ICD-10, and DRG codes.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎭</div>
                <h3>Emotional Intelligence</h3>
                <p>Adapts responses based on your emotional state and tone.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎙️</div>
                <h3>Voice Input Ready</h3>
                <p>Framework for voice processing and hands-free interaction.</p>
            </div>
        </div>
        """)
        
        # Control Section
        with gr.Row():
            reset_btn = gr.Button("🔄 Reset Conversation", elem_classes=["custom-button"])
            status_output = gr.Textbox(
                label="Status",
                placeholder="System status will appear here...",
                lines=1,
                interactive=False
            )
        
        # Usage Information
        gr.Markdown("""
        ### 💡 How to Use:
        - **Healthcare Codes**: Mention any billing code (A0429, 99213, etc.) and get detailed information
        - **General Questions**: Ask anything - from recipes to complex topics, I'm here to help!
        - **Emotional Support**: I adapt my tone based on your mood - express how you're feeling
        - **Voice Input**: Use the voice recorder for hands-free interaction (framework ready)
        - **Quick Lookup**: Use the code lookup tool for instant billing code information
        
        ### 🏥 Supported Code Types:
        - **CPT Codes**: Current Procedural Terminology (99213, 93000, etc.)
        - **HCPCS Codes**: Healthcare Common Procedure Coding (A0429, J3420, etc.)  
        - **ICD-10 Codes**: International Classification of Diseases (Z79.899, etc.)
        - **DRG Codes**: Diagnosis Related Groups (DRG470, etc.)
        """)
        
        # Event Handlers
        lookup_btn.click(
            quick_code_lookup,
            inputs=[code_input],
            outputs=[code_output]
        )
        
        voice_btn.click(
            process_voice_input,
            inputs=[audio_input],
            outputs=[voice_output]
        )
        
        reset_btn.click(
            reset_conversation,
            outputs=[status_output, code_output]
        )
    
    return demo
# ============= Launch Application =============

# Create and configure the interface
demo = create_gradio_interface()

# For Hugging Face Spaces, the app will be launched automatically
# No need for manual demo.launch() in Hugging Face Spaces
if __name__ == "__main__":
    # This block will be executed when running locally
    demo.launch(debug=True)