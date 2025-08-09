#!/usr/bin/env python3
"""
Ultimate AI Assistant - Medical Billing + General Knowledge
"""

import gradio as gr
import requests
import os
from typing import List, Tuple

# Configuration
API_KEY = os.getenv('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')
MODEL = "openai/gpt-3.5-turbo"  # Try "anthropic/claude-3-sonnet" for better answers

class AIAssistant:
    def __init__(self):
        self.system_prompt = """You are an expert AI with two specialties:
1. Medical billing codes (CPT, HCPCS, ICD, DRG)
2. General knowledge (science, tech, history, etc)

For medical questions:
- Always mention the code type
- Give official description
- Add practical examples

For other topics:
- Be concise but helpful
- Use bullet points when helpful
- Never make up facts"""
        
    def get_api_response(self, message: str) -> str:
        """Get intelligent response from API"""
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization': f'Bearer {API_KEY}'},
                json={
                    'model': MODEL,
                    'messages': [
                        {'role': 'system', 'content': self.system_prompt},
                        {'role': 'user', 'content': message}
                    ],
                    'temperature': 0.5
                },
                timeout=20
            )
            return response.json()['choices'][0]['message']['content']
        except:
            return self.get_fallback_response(message)
    
    def get_fallback_response(self, message: str) -> str:
        """When API fails"""
        medical_keywords = ['cpt', 'hcpcs', 'icd', 'drg', 'billing', 'medical code']
        
        if any(kw in message.lower() for kw in medical_keywords):
            return """🚑 Medical Billing Help (offline mode):
            
• CPT Codes: 99213 (Office Visit), 99214 (Extended Visit)
• HCPCS: A0429 (Ambulance), J3420 (Vitamin B12 Injection)
• ICD-10: Z23 (Immunization), E11.65 (Diabetes)

Ask about any code for details!"""
        else:
            return "🔍 I can discuss:\n- Science & Tech\n- History\n- Business\n- Culture\n\n(API connection offline - normal service will resume shortly)"

def chat_fn(message: str, history: List[Tuple[str, str]]) -> str:
    assistant = AIAssistant()
    return assistant.get_api_response(message)

# Modern Interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🧠 Hybrid AI Assistant
    *Medical billing expert + general knowledge*
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500)
            query = gr.Textbox(label="Ask about medical codes or any topic", placeholder="What's CPT 99213? Or ask about anything...")
            clear_btn = gr.ClearButton([query, chatbot])
            
        with gr.Column(scale=1):
            gr.Examples(
                examples=[
                    ["Explain CPT 99213 in detail"],
                    ["What's the capital of France?"],
                    ["Tell me about quantum computing"],
                    ["Difference between HCPCS and ICD codes"]
                ],
                inputs=query
            )
    
    query.submit(chat_fn, [query, chatbot], [query, chatbot])

# Launch
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
else:
    demo.launch()