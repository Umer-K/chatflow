#!/usr/bin/env python3
"""
Healthcare Billing Chatbot - Hugging Face Spaces App
Main application file for Hugging Face Spaces deployment
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
from datetime import datetime, timedelta
from pathlib import Path

# Set up environment variables (for Hugging Face Spaces)
os.environ['OPENROUTER_API_KEY'] = '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'
os.environ['DATA_SOURCE'] = 'local_csv'
os.environ['DATA_PATH'] = 'data/sample_codes.csv'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============= Data Classes and Enums =============

class ExplanationLength(Enum):
    SHORT = "short"
    DETAILED = "detailed"
    EXTRA = "extra"

class CodeType(Enum):
    CPT = "CPT"
    HCPCS = "HCPCS"
    ICD10 = "ICD-10"
    DRG = "DRG"
    UNKNOWN = "UNKNOWN"

class DataSource(Enum):
    LOCAL_CSV = "local_csv"
    LOCAL_JSON = "local_json"
    API = "api"

@dataclass
class ConversationContext:
    current_code: Optional[str] = None
    current_code_type: Optional[CodeType] = None
    current_code_info: Optional['CodeInfo'] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    last_explanation_length: Optional[ExplanationLength] = None
    turn_count: int = 0

@dataclass
class CodeInfo:
    code: str
    description: str
    code_type: str
    additional_info: Optional[str] = None
    effective_date: Optional[str] = None
    category: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'description': self.description,
            'code_type': self.code_type,
            'additional_info': self.additional_info,
            'effective_date': self.effective_date,
            'category': self.category
        }

# ============= HCPCS Loader Module =============

class HCPCSLoader:
    """Loader for HCPCS/CPT/ICD-10/DRG codes"""
    
    def __init__(self):
        self.data_source = DataSource(os.getenv('DATA_SOURCE', 'local_csv'))
        self.data_path = os.getenv('DATA_PATH', 'data/sample_codes.csv')
        self.codes_cache: Dict[str, CodeInfo] = {}
        self.cache_timestamp: Optional[datetime] = None
    
    def load_data(self) -> bool:
        """Load data from configured source"""
        try:
            return self._load_sample_data()
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return self._load_sample_data()
    
    def _load_sample_data(self) -> bool:
        """Load sample data as fallback"""
        logger.info("Loading sample data")
        
        sample_codes = {
            'A0429': CodeInfo(
                code='A0429',
                description='Ambulance service, basic life support, emergency transport (BLS-emergency)',
                code_type='HCPCS',
                additional_info='Ground ambulance emergency transport with BLS level care',
                category='Ambulance Services'
            ),
            'A0428': CodeInfo(
                code='A0428',
                description='Ambulance service, basic life support, non-emergency transport (BLS)',
                code_type='HCPCS',
                additional_info='Ground ambulance non-emergency transport with BLS level care',
                category='Ambulance Services'
            ),
            '99213': CodeInfo(
                code='99213',
                description='Office or other outpatient visit for evaluation and management, established patient, low complexity',
                code_type='CPT',
                additional_info='Typically 20-29 minutes with patient',
                category='E&M Services'
            ),
            '99214': CodeInfo(
                code='99214',
                description='Office or other outpatient visit for evaluation and management, established patient, moderate complexity',
                code_type='CPT',
                additional_info='Typically 30-39 minutes with patient',
                category='E&M Services'
            ),
            '93000': CodeInfo(
                code='93000',
                description='Electrocardiogram, routine ECG with at least 12 leads; with interpretation and report',
                code_type='CPT',
                additional_info='Complete ECG service including tracing, interpretation, and report',
                category='Cardiovascular'
            ),
            'DRG470': CodeInfo(
                code='DRG470',
                description='Major hip and knee joint replacement or reattachment of lower extremity without MCC',
                code_type='DRG',
                additional_info='Medicare Severity-Diagnosis Related Group for joint replacement procedures',
                category='Orthopedic'
            ),
            'Z79.899': CodeInfo(
                code='Z79.899',
                description='Other long term (current) drug therapy',
                code_type='ICD-10',
                additional_info='Used to indicate patient is on long-term medication therapy',
                category='Factors influencing health status'
            ),
            'E1399': CodeInfo(
                code='E1399',
                description='Durable medical equipment, miscellaneous',
                code_type='HCPCS',
                additional_info='DME not otherwise classified, requires detailed description',
                category='DME'
            ),
            'G0442': CodeInfo(
                code='G0442',
                description='Annual alcohol screening, 5 to 10 minutes',
                code_type='HCPCS',
                additional_info='Medicare-covered annual alcohol misuse screening',
                category='Preventive Services'
            ),
            '90837': CodeInfo(
                code='90837',
                description='Psychotherapy, 60 minutes with patient',
                code_type='CPT',
                additional_info='Individual psychotherapy session, 53-60 minutes',
                category='Psychiatric Services'
            ),
            'J3420': CodeInfo(
                code='J3420',
                description='Injection, vitamin B-12 cyanocobalamin, up to 1000 mcg',
                code_type='HCPCS',
                additional_info='Vitamin B12 injection for treatment of deficiency',
                category='Drug Administration'
            ),
            '80053': CodeInfo(
                code='80053',
                description='Comprehensive metabolic panel',
                code_type='CPT',
                additional_info='14 tests including glucose, kidney function, liver function, and electrolytes',
                category='Laboratory'
            ),
            'A0425': CodeInfo(
                code='A0425',
                description='Ground mileage, per statute mile',
                code_type='HCPCS',
                additional_info='Ambulance mileage for ground transport',
                category='Ambulance Services'
            ),
            '99215': CodeInfo(
                code='99215',
                description='Office visit, established patient, high complexity',
                code_type='CPT',
                additional_info='Typically 40-54 minutes with patient',
                category='E&M Services'
            ),
            '70450': CodeInfo(
                code='70450',
                description='CT scan head or brain without contrast',
                code_type='CPT',
                additional_info='Computed tomography of head/brain without contrast material',
                category='Radiology'
            )
        }
        
        self.codes_cache = sample_codes
        self.cache_timestamp = datetime.now()
        return True
    
    def lookup_code(self, code: str) -> Optional[CodeInfo]:
        """Look up a single code"""
        code = code.strip().upper()
        
        if code in self.codes_cache:
            return self.codes_cache[code]
        
        # Try with DRG prefix
        if code.startswith('DRG') and len(code) == 6:
            drg_code = code[3:]
            if drg_code in self.codes_cache:
                return self.codes_cache[drg_code]
        
        # Try adding DRG prefix
        if len(code) == 3 and code.isdigit():
            drg_code = f"DRG{code}"
            if drg_code in self.codes_cache:
                return self.codes_cache[drg_code]
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded codes"""
        stats = {
            'total_codes': len(self.codes_cache),
            'source': self.data_source.value,
            'codes_by_type': {}
        }
        
        for code_info in self.codes_cache.values():
            code_type = code_info.code_type
            stats['codes_by_type'][code_type] = stats['codes_by_type'].get(code_type, 0) + 1
        
        return stats

# ============= Code Classifier =============

class CodeClassifier:
    """Classifies and validates healthcare billing codes"""
    
    PATTERNS = {
        CodeType.CPT: re.compile(r'^[0-9]{5}$'),
        CodeType.HCPCS: re.compile(r'^[A-V][0-9]{4}$', re.IGNORECASE),
        CodeType.ICD10: re.compile(r'^[A-Z][0-9]{2}\.?[0-9]{0,3}$', re.IGNORECASE),
        CodeType.DRG: re.compile(r'^(?:DRG)?[0-9]{3}$', re.IGNORECASE),
    }
    
    @classmethod
    def classify_code(cls, code: str) -> CodeType:
        """Classify a code based on its format"""
        code = code.strip().upper()
        
        if code.startswith('DRG'):
            code = code[3:]
            if cls.PATTERNS[CodeType.DRG].match(f"DRG{code}"):
                return CodeType.DRG
        
        for code_type, pattern in cls.PATTERNS.items():
            if pattern.match(code):
                return code_type
        
        return CodeType.UNKNOWN
    
    @classmethod
    def extract_codes_from_text(cls, text: str) -> List[Tuple[str, CodeType]]:
        """Extract potential codes from free-form text"""
        codes = []
        
        patterns = [
            r'\b([A-V][0-9]{4})\b',  # HCPCS
            r'\b([0-9]{5})\b',  # CPT
            r'\bDRG\s*([0-9]{3})\b',  # DRG
            r'\b([A-Z][0-9]{2}\.?[0-9]{0,3})\b',  # ICD-10
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                code_type = cls.classify_code(match)
                if code_type != CodeType.UNKNOWN:
                    codes.append((match.upper(), code_type))
        
        return codes

# ============= OpenRouter Client =============

class OpenRouterClient:
    """Client for OpenRouter LLM API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY', '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')
        self.base_url = 'https://openrouter.ai/api/v1'
        self.model = 'openai/gpt-3.5-turbo'
        self.temperature = 0.3
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://huggingface.co',
            'X-Title': 'Healthcare Billing Chatbot'
        }
    
    def generate_explanation(self, 
                            code: str, 
                            code_type: CodeType,
                            code_info: Optional[CodeInfo],
                            length: ExplanationLength,
                            context: Optional[ConversationContext] = None) -> str:
        """Generate explanation using LLM"""
        
        if not code_info:
            return f"I couldn't find code {code} in our database. This might be an invalid code or one that's not in our current dataset."
        
        prompt = self._build_prompt(code, code_type, code_info, length, context)
        
        max_tokens = {
            ExplanationLength.SHORT: 150,
            ExplanationLength.DETAILED: 300,
            ExplanationLength.EXTRA: 500
        }.get(length, 200)
        
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self._get_system_prompt()},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': self.temperature,
            'max_tokens': max_tokens
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            explanation = result['choices'][0]['message']['content']
            return explanation
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return self._get_fallback_explanation(code, code_type, code_info, length)
    
    def _get_system_prompt(self) -> str:
        return """You are a healthcare billing expert assistant. Provide accurate, 
        fact-based explanations of healthcare billing codes. Only provide information 
        you are certain about. Be concise but informative. Use plain language."""
    
    def _build_prompt(self, code: str, code_type: CodeType, code_info: CodeInfo, 
                     length: ExplanationLength, context: Optional[ConversationContext]) -> str:
        
        base_prompt = f"""Healthcare Billing Code: {code}
Type: {code_type.value}
Official Description: {code_info.description}
Additional Information: {code_info.additional_info or 'N/A'}
"""
        
        if length == ExplanationLength.SHORT:
            base_prompt += "\nProvide a SHORT explanation (3-4 lines) in simple terms."
        elif length == ExplanationLength.DETAILED:
            base_prompt += "\nProvide a DETAILED explanation including what it covers and when it's typically used."
        elif length == ExplanationLength.EXTRA:
            base_prompt += "\nProvide EXTENDED details with sections for: typical use cases, coverage warnings, and important notes."
        
        return base_prompt
    
    def _get_fallback_explanation(self, code: str, code_type: CodeType, 
                                 code_info: CodeInfo, length: ExplanationLength) -> str:
        if length == ExplanationLength.SHORT:
            return f"{code} ({code_type.value}): {code_info.description[:150]}"
        else:
            explanation = f"{code} ({code_type.value}): {code_info.description}"
            if code_info.additional_info:
                explanation += f"\n\nAdditional Details: {code_info.additional_info}"
            return explanation

# ============= Main Chatbot Class =============

class HealthcareBillingChatbot:
    """Main chatbot class"""
    
    def __init__(self):
        self.loader = HCPCSLoader()
        self.classifier = CodeClassifier()
        self.llm_client = OpenRouterClient()
        self.context = ConversationContext()
        self.loader.load_data()
    
    def process_input(self, user_input: str) -> str:
        """Process user input and generate response"""
        self.context.turn_count += 1
        
        codes = self.classifier.extract_codes_from_text(user_input)
        intent = self._determine_intent(user_input, codes)
        response = self._generate_response(user_input, codes, intent)
        
        self.context.conversation_history.append({
            'user': user_input,
            'assistant': response
        })
        
        if len(self.context.conversation_history) > 10:
            self.context.conversation_history = self.context.conversation_history[-10:]
        
        return response
    
    def _determine_intent(self, user_input: str, codes: List[Tuple[str, CodeType]]) -> str:
        """Determine user intent"""
        lower_input = user_input.lower()
        
        if self.context.current_code:
            if any(keyword in lower_input for keyword in ['more', 'detail', 'explain']):
                return 'more_details'
        
        if any(keyword in lower_input for keyword in ['short', 'brief', 'quick']):
            return 'explain_short'
        if any(keyword in lower_input for keyword in ['detail', 'comprehensive']):
            return 'explain_detailed'
        
        if codes:
            return 'explain_code'
        
        return 'general_query'
    
    def _generate_response(self, user_input: str, codes: List[Tuple[str, CodeType]], intent: str) -> str:
        """Generate response based on intent"""
        
        if codes and intent in ['explain_code', 'explain_short', 'explain_detailed']:
            code, code_type = codes[0]
            code_info = self.loader.lookup_code(code)
            
            if not code_info:
                return f"I couldn't find code {code} in our database. Please check the code and try again."
            
            self.context.current_code = code
            self.context.current_code_type = code_type
            self.context.current_code_info = code_info
            
            length = ExplanationLength.SHORT
            if intent == 'explain_detailed':
                length = ExplanationLength.DETAILED
            
            explanation = self.llm_client.generate_explanation(
                code, code_type, code_info, length, self.context
            )
            
            if length != ExplanationLength.EXTRA:
                explanation += "\n\nWould you like more details about this code?"
            
            return explanation
        
        if self.context.current_code and intent == 'more_details':
            if not self.context.current_code_info:
                return "Please specify a code first."
            
            return self.llm_client.generate_explanation(
                self.context.current_code,
                self.context.current_code_type,
                self.context.current_code_info,
                ExplanationLength.EXTRA,
                self.context
            )
        
        return self._handle_general_query(user_input)
    
    def _handle_general_query(self, user_input: str) -> str:
        """Handle general queries"""
        lower_input = user_input.lower()
        
        if any(keyword in lower_input for keyword in ['help', 'how']):
            return """I can help you understand healthcare billing codes! You can:
• Ask about specific codes (e.g., "What is HCPCS A0429?")
• Request short or detailed explanations
• Ask follow-up questions about codes we've discussed

Just type a code or ask a question to get started!"""
        
        if any(keyword in lower_input for keyword in ['hello', 'hi', 'hey']):
            return "Hello! I'm here to help you understand healthcare billing codes. Feel free to ask about any CPT, HCPCS, ICD-10, or DRG code."
        
        return "I'm designed to help explain healthcare billing codes. Please provide a specific code (like A0429, 99213, or DRG470) and I'll give you a clear explanation."

# ============= Gradio Interface =============

def create_gradio_interface():
    """Create and return the Gradio interface"""
    chatbot = HealthcareBillingChatbot()
    
    def process_message(message: str, history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
        """Process a message and update chat history"""
        if not message:
            return "", history
        
        try:
            response = chatbot.process_input(message)
            history.append((message, response))
            return "", history
        except Exception as e:
            logger.error(f"Error: {e}")
            error_msg = "I apologize, but I encountered an error. Please try again."
            history.append((message, error_msg))
            return "", history
    
    def clear_conversation():
        """Clear the conversation"""
        chatbot.context = ConversationContext()
        return None
    
    # Create the interface
    with gr.Blocks(title="Healthcare Billing Chatbot", theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
            # 🏥 Healthcare Billing Chatbot
            
            Ask me about healthcare billing codes (CPT, HCPCS, ICD-10, DRG) and I'll provide clear explanations!
            
            ### Example Queries:
            - "What is HCPCS code A0429?"
            - "Explain CPT 99213 in detail"
            - "Tell me about DRG 470"
            """
        )
        
        chatbot_ui = gr.Chatbot(label="Conversation", height=400)
        
        with gr.Row():
            msg = gr.Textbox(
                label="Your Message",
                placeholder="Type a billing code or ask a question...",
                lines=2,
                scale=4
            )
            submit_btn = gr.Button("Send", variant="primary", scale=1)
        
        with gr.Row():
            clear_btn = gr.Button("🔄 Clear Conversation")
            
            with gr.Column():
                gr.Examples(
                    examples=[
                        "What is HCPCS A0429?",
                        "Explain CPT 99213",
                        "Tell me about DRG 470",
                        "What does code 93000 mean?",
                        "Give me more details"
                    ],
                    inputs=msg
                )
        
        # Event handlers
        msg.submit(process_message, [msg, chatbot_ui], [msg, chatbot_ui])
        submit_btn.click(process_message, [msg, chatbot_ui], [msg, chatbot_ui])
        clear_btn.click(clear_conversation, outputs=[chatbot_ui])
        
        stats = chatbot.loader.get_statistics()
        gr.Markdown(
            f"""
            ---
            **Database Info:** {stats['total_codes']} codes loaded | 
            Types: {', '.join(stats['codes_by_type'].keys())}
            """
        )
    
    return interface

# Launch the app
interface = create_gradio_interface()
interface.launch()