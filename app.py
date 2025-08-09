#!/usr/bin/env python3
"""
Simple GPT-3.5 Chatbot - No Medical, Just Clean Chat
"""

import gradio as gr
import requests
import os

# Configuration
API_KEY = os.getenv('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')  # Set in Spaces secrets
MODEL = "openai/gpt-3.5-turbo"

def respond(message, history):
    """Basic chat function that works with or without API"""
    if not API_KEY:
        return "Error: API key not configured (set OPENROUTER_API_KEY in secrets)"
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': MODEL,
                'messages': [{"role": "user", "content": message}],
                'temperature': 0.7
            },
            timeout=30
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Standard Gradio ChatInterface
demo = gr.ChatInterface(
    fn=respond,
    title="💬 Simple AI Chatbot",
    description="Talk about anything (using GPT-3.5-turbo)",
    examples=[
        "What's the meaning of life?",
        "Tell me a joke",
        "Explain quantum physics simply"
    ],
    theme="soft"
)

if __name__ == "__main__":
    demo.launch()
else:
    demo.launch()