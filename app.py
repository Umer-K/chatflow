#!/usr/bin/env python3
"""
Simplified Hybrid AI Assistant for Hugging Face Spaces
"""

import gradio as gr
from datetime import datetime
import random

# Simplified assistant responses
def chat_with_assistant(message, history):
    """Basic chat function that responds to messages"""
    if not message.strip():
        return "Please ask me a question about healthcare billing or anything else!"
    
    # Simple keyword responses
    lower_msg = message.lower()
    
    if any(word in lower_msg for word in ['hello', 'hi', 'hey']):
        return random.choice([
            "Hello! How can I help you today?",
            "Hi there! What can I assist you with?",
            "Hey! Ask me about healthcare billing codes or anything else."
        ])
    
    if any(word in lower_msg for word in ['code', 'cpt', 'hcpcs', 'icd', 'drg']):
        return "I can help with healthcare billing codes! For example:\n\n" + \
               "• CPT 99213: Office visit for established patient, low complexity\n" + \
               "• HCPCS A0429: Ambulance service, basic life support\n" + \
               "• DRG 470: Major hip/knee replacement without complications\n\n" + \
               "Ask me about a specific code for more details!"
    
    if 'thank' in lower_msg:
        return random.choice([
            "You're welcome! Let me know if you need anything else.",
            "Happy to help! Feel free to ask more questions.",
            "Glad I could assist! What else can I help with?"
        ])
    
    # Default response
    return random.choice([
        "I'm an AI assistant that can help with healthcare billing codes and general questions.",
        "I specialize in medical billing codes but can chat about other topics too!",
        "Ask me about CPT, HCPCS, ICD, or DRG codes for billing information."
    ])

# Create simple interface
demo = gr.ChatInterface(
    fn=chat_with_assistant,
    title="🏥 Healthcare Billing Assistant",
    description="Ask about medical billing codes or anything else!",
    examples=[
        "What is CPT code 99213?",
        "Explain HCPCS A0429",
        "Tell me about DRG 470",
        "Hello!"
    ]
)

# Launch for Hugging Face Spaces
if __name__ == "__main__":
    demo.launch(debug=True)
else:
    demo.launch()