#!/usr/bin/env python3
"""
Ultra-Reliable Chatbot - No Medical, No Errors
"""

import gradio as gr
import requests
import os

API_KEY = os.getenv('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')  # Set in Spaces secrets
MODEL = "openai/gpt-3.5-turbo"

def respond(message, history):
    """Foolproof response function"""
    if not message.strip():
        return "Please type something..."
    
    if not API_KEY:
        return "🔴 API key not configured (set OPENROUTER_API_KEY secret)"
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json={
                'model': MODEL,
                'messages': [{"role": "user", "content": message}],
                'temperature': 0.7,
                'max_tokens': 500
            },
            timeout=10  # Shorter timeout to prevent hanging
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"🔴 API Error (Status: {response.status_code})"
            
    except requests.exceptions.RequestException as e:
        return f"⚠️ Connection error: {str(e)}"
    except Exception as e:
        return f"⚠️ Unexpected error: {str(e)}"

# Standard Gradio interface
demo = gr.ChatInterface(
    fn=respond,
    title="💬 Simple AI Chat",
    examples=["Hello!", "Tell me about yourself", "What's 2+2?"],
    retry_btn=None,
    undo_btn=None
)

demo.launch()