import os
import requests
import gradio as gr

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-3.5-turbo"

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set. Please set it before running.")

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

def query_openrouter(messages):
    payload = {
        "model": MODEL,
        "messages": messages
    }
    response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")
    data = response.json()
    return data["choices"][0]["message"]["content"]

def chatbot_response(message, history):
    if not message.strip():
        return history, ""
    
    # Convert history to API format
    api_messages = []
    for h in history:
        if h[0]:  # User message
            api_messages.append({"role": "user", "content": h[0]})
        if h[1]:  # Assistant message  
            api_messages.append({"role": "assistant", "content": h[1]})
    
    # Add current message
    api_messages.append({"role": "user", "content": message})
    
    # Get response
    bot_reply = query_openrouter(api_messages)
    
    # Add to history
    history.append([message, bot_reply])
    
    return history, ""

# Simple, working modern chatbot CSS
css = """
/* Modern 2025 AI Chatbot - Simple & Working */
.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background: #ffffff !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Hide Gradio branding */
footer, .gradio-container .prose {
    display: none !important;
}

/* Main container */
.main-container {
    max-width: 800px !important;
    margin: 0 auto !important;
    height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    background: #ffffff !important;
}

/* Header */
.header {
    padding: 20px 24px !important;
    text-align: center !important;
    border-bottom: 1px solid #e5e7eb !important;
    background: #ffffff !important;
}

.header h1 {
    font-size: 24px !important;
    font-weight: 600 !important;
    color: #111827 !important;
    margin: 0 !important;
}

/* Chat area */
.chat-section {
    flex: 1 !important;
    padding: 0 !important;
    overflow: hidden !important;
    background: #ffffff !important;
}

.gr-chatbot {
    height: 60vh !important;
    border: none !important;
    background: transparent !important;
    padding: 24px !important;
    overflow-y: auto !important;
}

/* Message bubbles */
.gr-chatbot .message {
    margin: 16px 0 !important;
    padding: 12px 18px !important;
    border-radius: 18px !important;
    max-width: 75% !important;
    font-size: 15px !important;
    line-height: 1.5 !important;
    word-wrap: break-word !important;
}

/* User messages - blue, right aligned */
.gr-chatbot .message:nth-child(odd) {
    background: #2563eb !important;
    color: #ffffff !important;
    margin-left: auto !important;
    margin-right: 0 !important;
    border-bottom-right-radius: 4px !important;
}

/* Bot messages - gray, left aligned, wider */
.gr-chatbot .message:nth-child(even) {
    background: #f1f3f4 !important;
    color: #374151 !important;
    margin-left: 0 !important;
    margin-right: auto !important;
    border-bottom-left-radius: 4px !important;
    max-width: 85% !important;
    border: 1px solid #e5e7eb !important;
}

/* Input section */
.input-section {
    padding: 16px 24px 24px 24px !important;
    background: #ffffff !important;
    border-top: 1px solid #e5e7eb !important;
}

.input-row {
    display: flex !important;
    gap: 8px !important;
    align-items: flex-end !important;
    position: relative !important;
}

/* Text input */
.gr-textbox {
    flex: 1 !important;
    padding: 12px 50px 12px 16px !important;
    border: 1px solid #d1d5db !important;
    border-radius: 24px !important;
    font-size: 15px !important;
    background: #ffffff !important;
    outline: none !important;
    resize: none !important;
    transition: border-color 0.2s ease !important;
}

.gr-textbox:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
}

.gr-textbox::placeholder {
    color: #9ca3af !important;
}

/* Send button */
.gr-button {
    position: absolute !important;
    right: 4px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    border-radius: 18px !important;
    background: #2563eb !important;
    border: none !important;
    color: #ffffff !important;
    font-size: 18px !important;
    cursor: pointer !important;
    transition: background-color 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
}

.gr-button:hover {
    background: #1d4ed8 !important;
}

.gr-button:active {
    background: #1e40af !important;
}

/* Scrollbar */
.gr-chatbot::-webkit-scrollbar {
    width: 4px;
}

.gr-chatbot::-webkit-scrollbar-track {
    background: transparent;
}

.gr-chatbot::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 2px;
}

.gr-chatbot::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .main-container {
        max-width: 100% !important;
    }
    
    .header, .input-section {
        padding-left: 16px !important;
        padding-right: 16px !important;
    }
    
    .gr-chatbot {
        padding: 16px !important;
        height: 55vh !important;
    }
    
    .gr-chatbot .message {
        max-width: 85% !important;
    }
    
    .gr-chatbot .message:nth-child(even) {
        max-width: 90% !important;
    }
}

/* Animation */
.gr-chatbot .message {
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
"""

# Create clean, working interface
with gr.Blocks(css=css, title="💬 Aesthetic AI Chatbot") as demo:
    
    with gr.Column(elem_classes=["main-container"]):
        
        # Clean header
        with gr.Row(elem_classes=["header"]):
            gr.Markdown("# 💬 Aesthetic AI Chatbot")
        
        # Chat area
        with gr.Column(elem_classes=["chat-section"]):
            chatbot = gr.Chatbot(
                elem_classes=["gr-chatbot"],
                show_label=False,
                container=False,
                bubble_full_width=False,
                show_copy_button=False
            )
        
        # Input section
        with gr.Column(elem_classes=["input-section"]):
            with gr.Row(elem_classes=["input-row"]):
                msg = gr.Textbox(
                    placeholder="Message Aesthetic AI...",
                    show_label=False,
                    container=False,
                    lines=1,
                    max_lines=4,
                    scale=1
                )
                send = gr.Button("↑", size="sm")

    # Simple event handling
    def handle_message(message, history):
        if not message.strip():
            return history, ""
        return chatbot_response(message, history)

    # Connect events
    msg.submit(handle_message, [msg, chatbot], [chatbot, msg])
    send.click(handle_message, [msg, chatbot], [chatbot, msg])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
        show_error=True
    )