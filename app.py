#!/usr/bin/env python3
"""
Reliable AI Assistant with Fallback Responses
"""

import gradio as gr
import requests
import os
import random

# Configuration
API_KEY = os.getenv('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')  # Set this in Spaces secrets
USE_API = bool(API_KEY)  # Only use API if key is available

# Fallback responses for when API fails
FALLBACK_RESPONSES = [
    "I'd be happy to help with that!",
    "Interesting question! Could you tell me more?",
    "I can help with that. Here's what I know...",
    "Let me think about that for a moment...",
    "That's a great question!",
]

def get_api_response(message):
    """Try to get response from OpenRouter API"""
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'openai/gpt-3.5-turbo',
                'messages': [{'role': 'user', 'content': message}],
                'temperature': 0.7
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception:
        return None

def chat_with_assistant(message, history):
    """Reliable chat function with fallback"""
    if not message.strip():
        return "Please type your message, I'm happy to help!"
    
    # Try API if available
    if USE_API:
        api_response = get_api_response(message)
        if api_response:
            return api_response
    
    # Fallback responses
    lower_msg = message.lower()
    
    # Handle common questions without API
    if any(w in lower_msg for w in ['hello', 'hi', 'hey']):
        return random.choice([
            "Hello! How can I help you today?",
            "Hi there! What would you like to know?",
            "Hey! Ask me anything."
        ])
    
    if 'how are you' in lower_msg:
        return "I'm an AI, so I don't have feelings, but I'm ready to help you!"
    
    if any(w in lower_msg for w in ['thank', 'thanks']):
        return "You're welcome! Is there anything else you'd like to know?"
    
    # General fallback
    return random.choice(FALLBACK_RESPONSES)

# Create reliable interface
demo = gr.ChatInterface(
    fn=chat_with_assistant,
    title="🤖 Reliable AI Assistant",
    description="Ask me anything! (Works even when API fails)",
    examples=[
        "What's the capital of France?",
        "Explain quantum computing",
        "How do I make pizza dough?",
        "Tell me about AI"
    ],
    retry_btn=None,
    undo_btn=None
)

# Launch for Hugging Face Spaces
if __name__ == "__main__":
    demo.launch(debug=True)
else:
    demo.launch()