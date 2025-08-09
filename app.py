#!/usr/bin/env python3
"""
Final Fixed AI Assistant - No Warnings, Clear Responses
"""

import gradio as gr
import requests
import os
import random
from datetime import datetime

# Configuration
API_KEY = os.getenv('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')
MODEL = "openai/gpt-3.5-turbo"  # Change to any OpenRouter model

# System message for API calls
SYSTEM_PROMPT = """You are a helpful AI assistant specializing in medical billing codes and general knowledge.
Respond concisely and clearly. For medical codes, provide:
1. Code type (CPT/HCPCS/ICD/DRG)
2. Official description
3. Common use cases
4. Any important notes"""

def get_api_response(message: str) -> str:
    """Get response from OpenRouter API"""
    if not API_KEY:
        raise ValueError("API key not configured")
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': MODEL,
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': message}
                ],
                'temperature': 0.7
            },
            timeout=15
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"API Error: {str(e)}")
        return "I'm having trouble connecting to my knowledge base. Please try again later."

def respond(message: str, history: list) -> str:
    """Main response function with clear output"""
    if not message.strip():
        return "Please type your question about medical billing or any other topic."
    
    # Medical billing keywords
    billing_keywords = ['cpt', 'hcpcs', 'icd', 'drg', 'medical code', 'billing']
    
    if any(kw in message.lower() for kw in billing_keywords):
        try:
            return get_api_response(message)
        except:
            return ("I can explain medical billing codes like:\n\n"
                   "• CPT 99213: Office visit\n"
                   "• HCPCS A0429: Ambulance\n"
                   "• ICD-10 Z23: Immunization\n\n"
                   "Ask about a specific code for details.")
    
    # General questions
    return get_api_response(message)

# Create modern chat interface
with gr.Blocks(title="Medical Coding Assistant") as demo:
    gr.Markdown("# 🏥 AI Medical Billing Assistant")
    gr.Markdown("Ask about healthcare codes or general topics")
    
    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(label="Your Question")
    clear = gr.ClearButton([msg, chatbot])
    
    msg.submit(respond, [msg, chatbot], [msg, chatbot])

# Launch properly
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
else:
    demo.launch()