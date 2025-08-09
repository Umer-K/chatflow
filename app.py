#!/usr/bin/env python3
"""
Hybrid AI Assistant - General Purpose + Healthcare Billing Expert
Gradio ChatInterface with Grok-like UI - HUGGING FACE SPACES VERSION
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
try:
    import whisper
except ImportError:
    whisper = None
    logging.warning("whisper not available; voice input will be disabled")
try:
    from gtts import gTTS
except ImportError:
    gTTS = None
    logging.warning("gTTS not available; voice output will be disabled")
from io import BytesIO

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
    chat_id: str = field(default_factory=lambda: f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

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
        self.contexts = {}  # Store multiple chat contexts by chat_id
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://huggingface.co',
            'X-Title': 'Hybrid AI Assistant'
        }
    
    def get_context(self, chat_id: str) -> ConversationContext:
        """Get or create a context for a given chat_id"""
        if chat_id not in self.contexts:
            self.contexts[chat_id] = ConversationContext(chat_id=chat_id)
        return self.contexts[chat_id]
    
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
    
    def get_general_response(self, message: str, chat_id: str, billing_context: bool = False) -> str:
        """Get response from OpenRouter API for general queries"""
        context = self.get_context(chat_id)
        
        # Analyze sentiment
        sentiment = self.sentiment_analyzer.analyze_sentiment(message)
        context.current_sentiment = sentiment.value
        context.sentiment_history.append(sentiment.value)
        
        # Keep only last 10 sentiments
        if len(context.sentiment_history) > 10:
            context.sentiment_history = context.sentiment_history[-10:]
        
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
        for msg in context.messages[-10:]:
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
                context.messages.append({'role': 'user', 'content': message})
                context.messages.append({'role': 'assistant', 'content': ai_response})
                
                # Keep only last 20 messages in context
                if len(context.messages) > 20:
                    context.messages = context.messages[-20:]
                
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
    
    def process_message(self, message: str, chat_id: str) -> Tuple[str, str]:
        """Main method to process any message and return response with sentiment"""
        if not message.strip():
            return "Feel free to ask me anything! I can help with general questions or healthcare billing codes. 😊", "neutral"
        
        # Detect intent
        intent = self.detect_intent(message)
        
        # Route to appropriate handler
        if intent['is_billing'] and intent['codes_found']:
            response = self.handle_billing_query(message, intent['codes_found'])
        else:
            response = self.get_general_response(message, chat_id, billing_context=intent['is_billing'])
        
        context = self.get_context(chat_id)
        return response, context.current_sentiment
    
    def reset_context(self, chat_id: str):
        """Reset conversation context for a specific chat"""
        if chat_id in self.contexts:
            del self.contexts[chat_id]
    
    def get_chat_history(self) -> List[str]:
        """Return list of chat IDs for display"""
        return list(self.contexts.keys())

# ============= Global Assistant Instance =============
assistant = HybridAIAssistant()

# ============= Chat Functions for Gradio =============

def chat_with_assistant(message: str, history: List[Tuple[str, str]], chat_id: str):
    """Main chat function for Gradio ChatInterface"""
    try:
        if not message or not message.strip():
            return "Feel free to ask me anything! I can help with general questions or healthcare billing codes. 😊", chat_id
        
        # Process message and get response
        response, sentiment = assistant.process_message(message.strip(), chat_id)
        return response, chat_id
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return "I apologize, but I encountered an error processing your message. Please try again!", chat_id

def process_voice_input(audio_file, chat_id: str):
    """Process voice input using Whisper"""
    if audio_file is None:
        return "No audio received. Please try recording again.", None, chat_id
    
    if whisper is None or gTTS is None:
        return "Voice interaction is not available in this environment. Please type your question.", None, chat_id
    
    try:
        # Load Whisper model
        model = whisper.load_model("base")
        
        # Transcribe audio
        result = model.transcribe(audio_file)
        text = result["text"]
        logger.info(f"Recognized text: {text}")
        
        # Process the recognized text through the assistant
        response, sentiment = assistant.process_message(text.strip(), chat_id)
        
        # Generate audio response
        tts = gTTS(text=response, lang='en')
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return response, audio_buffer, chat_id
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        return "Error processing voice input. Please try again.", None, chat_id

def start_new_chat():
    """Start a new chat session"""
    new_chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return new_chat_id, f"Started new chat: {new_chat_id}", []

def select_chat(chat_id: str):
    """Load a selected chat from history"""
    context = assistant.get_context(chat_id)
    history = [(msg['content'], msg['content']) for msg in context.messages if msg['role'] == 'user' and msg['content'] in [m['content'] for m in context.messages if m['role'] == 'assistant']]
    return chat_id, f"Loaded chat: {chat_id}", history

def reset_conversation(chat_id: str):
    """Reset the current conversation"""
    assistant.reset_context(chat_id)
    new_chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return new_chat_id, "✅ Conversation reset successfully!", []

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

# ============= Custom CSS for Grok-like UI =============
custom_css = """
/* Grok-like UI for Hugging Face Spaces */
.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
    background: #f5f7fa !important;
    padding: 1rem !important;
    display: flex;
}

/* Sidebar (Left) */
.sidebar {
    width: 250px !important;
    background: #2c2f3b !important;
    color: white !important;
    padding: 1rem !important;
    border-radius: 8px !important;
    height: calc(100vh - 2rem) !important;
    overflow-y: auto !important;
    margin-right: 1rem !important;
}

.sidebar h2 {
    font-size: 1.5rem !important;
    margin-bottom: 1rem !important;
}

.sidebar select, .sidebar button {
    width: 100% !important;
    padding: 0.5rem !important;
    margin-bottom: 0.5rem !important;
    border-radius: 5px !important;
    background: #3b3e4a !important;
    color: white !important;
    border: none !important;
}

.sidebar button:hover {
    background: #4a4d5a !important;
}

/* Chat Area (Right) */
.chat-container {
    flex-grow: 1 !important;
    background: white !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    padding: 1rem !important;
}

.gradio-chatbot {
    min-height: 500px !important;
    font-size: 1.1rem !important;
}

.gradio-chatbot .message {
    margin-bottom: 1rem !important;
    padding: 0.8rem !important;
    border-radius: 8px !important;
}

.gradio-chatbot .user-message {
    background: #e6f3ff !important;
    text-align: right !important;
}

.gradio-chatbot .bot-message {
    background: #f0f0f0 !important;
    text-align: left !important;
}

.chat-input {
    width: 100% !important;
    padding: 0.8rem !important;
    font-size: 1rem !important;
}

/* Voice Section */
.voice-section {
    margin-top: 1rem !important;
    display: flex !important;
    gap: 1rem !important;
}

.custom-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.custom-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
}

/* Status */
.status-box {
    margin-top: 1rem !important;
    font-size: 0.9rem !important;
    color: #666 !important;
}

/* Responsive Design */
@media (max-width: 768px) {
    .gradio-container {
        flex-direction: column !important;
    }
    
    .sidebar {
        width: 100% !important;
        height: auto !important;
        margin-bottom: 1rem !important;
    }
    
    .chat-container {
        width: 100% !important;
    }
}
"""

# ============= Main Gradio Interface =============

def create_gradio_interface():
    """Create the main Gradio interface with Grok-like UI"""
    with gr.Blocks(css=custom_css, title="🏥 Hybrid AI Assistant") as demo:
        # State to track current chat ID
        chat_id_state = gr.State(value=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Main Layout with Sidebar and Chat
        with gr.Row():
            # Sidebar (Left)
            with gr.Column(elem_classes=["sidebar"], scale=1):
                gr.Markdown("## Chat History")
                chat_history = gr.Dropdown(
                    choices=assistant.get_chat_history(),
                    label="Select Chat",
                    value=chat_id_state.value,
                    interactive=True
                )
                new_chat_btn = gr.Button("New Chat", elem_classes=["custom-button"])
                reset_btn = gr.Button("Reset Current Chat", elem_classes=["custom-button"])
            
            # Chat Area (Right)
            with gr.Column(elem_classes=["chat-container"], scale=3):
                gr.Markdown("## 🏥 Hybrid AI Assistant")
                chatbot = gr.ChatInterface(
                    fn=chat_with_assistant,
                    additional_inputs=[chat_id_state],
                    examples=examples,
                    title="",
                    description="💬 Ask about healthcare billing codes or anything else! I'm here to help with a friendly vibe. 😎"
                )
                
                # Voice Interaction (Optional)
                if whisper is not None and gTTS is not None:
                    gr.Markdown("### 🎙️ Voice Interaction")
                    with gr.Row(elem_classes=["voice-section"]):
                        audio_input = gr.Audio(
                            sources=["microphone"],
                            type="filepath",
                            label="Speak to the Assistant"
                        )
                        audio_output = gr.Audio(
                            label="Assistant's Response",
                            type="filepath",
                            interactive=False
                        )
                        voice_btn = gr.Button("🎤 Process Voice", elem_classes=["custom-button"])
                
                status_output = gr.Textbox(
                    label="Status",
                    placeholder="System status will appear here...",
                    lines=1,
                    interactive=False,
                    elem_classes=["status-box"]
                )
        
        # Event Handlers
        new_chat_btn.click(
            fn=start_new_chat,
            outputs=[chat_id_state, status_output, chatbot]
        )
        reset_btn.click(
            fn=reset_conversation,
            inputs=[chat_id_state],
            outputs=[chat_id_state, status_output, chatbot]
        )
        chat_history.change(
            fn=select_chat,
            inputs=[chat_history],
            outputs=[chat_id_state, status_output, chatbot]
        )
        if whisper is not None and gTTS is not None:
            voice_btn.click(
                fn=process_voice_input,
                inputs=[audio_input, chat_id_state],
                outputs=[chatbot, audio_output, chat_id_state]
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