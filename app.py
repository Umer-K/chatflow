#!/usr/bin/env python3
"""
General Purpose AI Assistant - First Phase
"""

import gradio as gr
import requests
import os

# Configure API
API_KEY = os.getenv('OPENROUTER_API_KEY', 'k-or-v1-e2161963164f8d143197fe86376d195117f60a96f54f984776de22e4d9ab96a3')
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'HTTP-Referer': 'https://huggingface.co',
    'X-Title': 'AI Assistant'
}

def chat_with_assistant(message, history):
    """General purpose chat function using OpenRouter API"""
    if not message.strip():
        return "Please type your message, I'm happy to chat about anything!"
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=HEADERS,
            json={
                'model': 'openai/gpt-3.5-turbo',
                'messages': [{
                    'role': 'user',
                    'content': message
                }],
                'temperature': 0.7
            }
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"I encountered an error (Status: {response.status_code}). Please try again."
            
    except Exception as e:
        return f"Sorry, I'm having trouble responding right now. Error: {str(e)}"

# Create interface
demo = gr.ChatInterface(
    fn=chat_with_assistant,
    title="🤖 General AI Assistant",
    description="I can chat about anything! We'll soon add healthcare billing expertise.",
    examples=[
        "What's the nutrition value of apples?",
        "Who is Elon Musk?",
        "Explain quantum computing simply",
        "What are some good books to read?"
    ]
)

# Launch for Hugging Face Spaces
if __name__ == "__main__":
    demo.launch(debug=True)
else:
    demo.launch()