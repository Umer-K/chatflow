#!/usr/bin/env python3
"""
Fully Functional AI Assistant with Reliable API Integration
"""

import gradio as gr
import requests
import os
import random
from typing import Optional

# Configuration - SET YOUR API KEY IN HUGGINGFACE SPACES SECRETS
API_KEY = os.getenv('OPENROUTER_API_KEY')
API_ENABLED = bool(API_KEY)  # Auto-disable if no API key

# Model Configuration
MODEL = "openai/gpt-3.5-turbo"  # Change to any OpenRouter supported model

# Fallback responses
FALLBACK_RESPONSES = [
    "I'd be happy to help with that!",
    "Interesting question! Here's what I know...",
    "Let me share some information about that...",
    "I can help with that. What specifically would you like to know?",
]

def get_api_response(message: str) -> Optional[str]:
    """Get response from OpenRouter API with proper error handling"""
    if not API_ENABLED:
        return None
        
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://huggingface.co',
            },
            json={
                'model': MODEL,
                'messages': [{'role': 'user', 'content': message}],
                'temperature': 0.7,
                'max_tokens': 500,
            },
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"API Error: Status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"API Exception: {str(e)}")
        return None

def get_local_response(message: str) -> str:
    """Local knowledge base for when API fails"""
    lower_msg = message.lower()
    
    # Medical Billing Knowledge
    if any(word in lower_msg for word in ['cpt', 'hcpcs', 'icd', 'drg', 'medical code', 'billing']):
        return ("I can help with medical billing codes! Here are examples:\n\n"
                "• CPT 99213: Office visit (established patient)\n"
                "• HCPCS A0429: Emergency ambulance transport\n"
                "• ICD-10 Z23: Encounter for immunization\n\n"
                "Ask about a specific code for details!")
    
    # General Knowledge
    knowledge = {
        'elon musk': "Elon Musk is CEO of SpaceX/Tesla. Known for EVs and space tech.",
        'apple nutrition': "Medium apple (182g):\n- Calories: 95\n- Fiber: 4g\n- Vitamin C: 14% DV",
        'hello': random.choice(["Hello! How can I help?", "Hi there!", "Hey! Ask me anything."]),
        'thank you': "You're welcome!",
    }
    
    for keyword, response in knowledge.items():
        if keyword in lower_msg:
            return response
    
    return random.choice(FALLBACK_RESPONSES)

def chat_with_assistant(message: str, history: list) -> str:
    """Main chat function with API and local fallback"""
    if not message.strip():
        return "Please type your message. I can discuss medical billing or general topics!"
    
    # Try API first if enabled
    if API_ENABLED:
        api_response = get_api_response(message)
        if api_response:
            return api_response
    
    # Fallback to local knowledge
    return get_local_response(message)

# Create the interface
demo = gr.ChatInterface(
    fn=chat_with_assistant,
    title="🏥 AI Medical Billing Assistant",
    description=f"Using {MODEL} | Ask about healthcare codes or general topics",
    examples=[
        ["What is CPT 99213?"],
        ["Explain HCPCS A0429"],
        ["Tell me about Elon Musk"],
        ["Apple nutrition facts"],
    ],
)

# Launch with reliability
if __name__ == "__main__":
    demo.launch(debug=True)
else:
    demo.launch()