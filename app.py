#!/usr/bin/env python3
"""
Basic GPT-3.5 Chatbot - No Errors, Just Chat
"""

import gradio as gr
import requests
import os

# Configuration (paste your key here directly for testing)
API_KEY = "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"
MODEL = "openai/gpt-3.5-turbo"

def chat(message, history):
    """Simple API call with error handling"""
    try:
        response = requests.post(
            "https://api.openrouter.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.7
            },
            timeout=10
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

# Minimal Gradio interface
demo = gr.ChatInterface(
    fn=chat,
    title="Simple AI Chat",
    examples=["Hello!", "Tell me a joke", "Explain quantum physics"]
)

if __name__ == "__main__":
    demo.launch()
else:
    demo.launch()