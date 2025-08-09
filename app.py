#!/usr/bin/env python3
"""
Hybrid AI Assistant - General Purpose + Healthcare Billing Expert
Enhanced with Emotional UI and Whisper Voice Input/Output - HUGGING FACE SPACES VERSION
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
        elif positive_count >