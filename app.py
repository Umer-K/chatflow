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

# Complete 2025 Modern Chatbot CSS
css = """
/* Complete Modern 2025 Chatbot Interface */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif !important;
    background: #ffffff !important;
    height: 100vh !important;
    overflow: hidden !important;
}

/* Hide all Gradio default elements */
footer, .gr-button-lg, .gradio-container .prose, 
.gradio-container > div:last-child,
.gradio-container > .gr-block > div:last-child {
    display: none !important;
}

/* Main layout container */
.main-layout {
    display: flex !important;
    height: 100vh !important;
    max-width: 100% !important;
    margin: 0 auto !important;
}

/* Left sidebar */
.sidebar {
    width: 260px !important;
    background: #f8f9fa !important;
    border-right: 1px solid #e9ecef !important;
    padding: 16px !important;
    overflow-y: auto !important;
    flex-shrink: 0 !important;
}

.sidebar h3 {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #6c757d !important;
    margin-bottom: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

.sidebar-item {
    padding: 8px 12px !important;
    border-radius: 6px !important;
    margin-bottom: 4px !important;
    color: #495057 !important;
    font-size: 14px !important;
    cursor: pointer !important;
    transition: background-color 0.1s ease !important;
}

.sidebar-item:hover {
    background: #e9ecef !important;
}

.sidebar-item.active {
    background: #e3f2fd !important;
    color: #1976d2 !important;
}

/* Main chat area */
.chat-main {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    max-width: 768px !important;
    margin: 0 auto !important;
    height: 100vh !important;
}

/* Header with logo and name */
.header {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 16px 24px !important;
    border-bottom: 1px solid #e9ecef !important;
    background: #ffffff !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 100 !important;
}

.header-content {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

.logo {
    width: 28px !important;
    height: 28px !important;
    font-size: 20px !important;
}

.header h1 {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: #212529 !important;
    margin: 0 !important;
}

/* Chat messages area */
.messages-container {
    flex: 1 !important;
    overflow-y: auto !important;
    padding: 0 !important;
    background: #ffffff !important;
}

.gr-chatbot {
    height: 100% !important;
    border: none !important;
    background: transparent !important;
    padding: 24px !important;
}

/* Message styling */
.gr-chatbot > div {
    display: flex !important;
    flex-direction: column !important;
    gap: 20px !important;
}

.message-wrapper {
    display: flex !important;
    width: 100% !important;
    animation: fadeIn 0.3s ease-out !important;
}

/* User messages (right side, blue bubbles) */
.message-wrapper:has(.user-message) {
    justify-content: flex-end !important;
}

.user-message {
    background: #2563eb !important;
    color: #ffffff !important;
    padding: 10px 14px !important;
    border-radius: 18px !important;
    border-bottom-right-radius: 4px !important;
    max-width: 70% !important;
    font-size: 15px !important;
    line-height: 1.4 !important;
    word-wrap: break-word !important;
}

/* AI messages (left side, gray bubbles, wider) */
.message-wrapper:has(.bot-message) {
    justify-content: flex-start !important;
}

.bot-message {
    background: #f1f3f4 !important;
    color: #3c4043 !important;
    padding: 12px 16px !important;
    border-radius: 18px !important;
    border-bottom-left-radius: 4px !important;
    max-width: 85% !important;
    font-size: 15px !important;
    line-height: 1.5 !important;
    word-wrap: break-word !important;
    border: 1px solid #e8eaed !important;
}

/* Input area at bottom */
.input-section {
    padding: 16px 24px 24px 24px !important;
    background: #ffffff !important;
    border-top: 1px solid #e9ecef !important;
    position: sticky !important;
    bottom: 0 !important;
}

.input-wrapper {
    position: relative !important;
    max-width: 100% !important;
}

/* Rounded input box */
.gr-textbox {
    width: 100% !important;
    padding: 12px 52px 12px 16px !important;
    border: 1px solid #dadce0 !important;
    border-radius: 24px !important;
    font-size: 15px !important;
    background: #ffffff !important;
    outline: none !important;
    transition: all 0.15s ease !important;
    resize: none !important;
    min-height: 44px !important;
    max-height: 120px !important;
    line-height: 1.4 !important;
}

.gr-textbox:focus {
    border-color: #1976d2 !important;
    box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.1) !important;
}

.gr-textbox::placeholder {
    color: #5f6368 !important;
}

/* Embedded arrow send button */
.send-btn {
    position: absolute !important;
    right: 6px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 32px !important;
    height: 32px !important;
    border-radius: 16px !important;
    background: #1976d2 !important;
    border: none !important;
    color: #ffffff !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 16px !important;
    transition: all 0.15s ease !important;
}

.send-btn:hover {
    background: #1565c0 !important;
    transform: translateY(-50%) scale(1.05) !important;
}

.send-btn:active {
    background: #0d47a1 !important;
    transform: translateY(-50%) scale(0.95) !important;
}

/* Smooth animations */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Custom scrollbar */
.messages-container::-webkit-scrollbar,
.sidebar::-webkit-scrollbar {
    width: 6px;
}

.messages-container::-webkit-scrollbar-track,
.sidebar::-webkit-scrollbar-track {
    background: transparent;
}

.messages-container::-webkit-scrollbar-thumb,
.sidebar::-webkit-scrollbar-thumb {
    background: #dadce0;
    border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover,
.sidebar::-webkit-scrollbar-thumb:hover {
    background: #bdc1c6;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .sidebar {
        display: none !important;
    }
    
    .chat-main {
        max-width: 100% !important;
    }
    
    .user-message {
        max-width: 80% !important;
    }
    
    .bot-message {
        max-width: 90% !important;
    }
    
    .header, .input-section {
        padding-left: 16px !important;
        padding-right: 16px !important;
    }
    
    .gr-chatbot {
        padding: 16px !important;
    }
}

/* Clean typography */
.gr-chatbot p {
    margin: 0 !important;
}

.gr-chatbot pre {
    background: #f8f9fa !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    overflow-x: auto !important;
}
"""

# Create the complete modern interface
with gr.Blocks(css=css, title="Aesthetic AI Chatbot") as demo:
    
    with gr.Row(elem_classes=["main-layout"]):
        # Left sidebar
        with gr.Column(elem_classes=["sidebar"]):
            gr.Markdown("### Chat History")
            gr.Markdown('<div class="sidebar-item active">Current Conversation</div>')
            gr.Markdown('<div class="sidebar-item">Previous Chat 1</div>')
            gr.Markdown('<div class="sidebar-item">Previous Chat 2</div>')
            gr.Markdown('<div class="sidebar-item">Previous Chat 3</div>')
            gr.Markdown("### Settings")
            gr.Markdown('<div class="sidebar-item">Model Settings</div>')
            gr.Markdown('<div class="sidebar-item">Export Chat</div>')
        
        # Main chat area
        with gr.Column(elem_classes=["chat-main"]):
            # Header with logo and name
            with gr.Row(elem_classes=["header"]):
                with gr.Column(elem_classes=["header-content"]):
                    gr.Markdown('<div class="logo">💬</div><h1>Aesthetic AI Chatbot</h1>', elem_classes=["header-content"])
            
            # Messages container
            with gr.Column(elem_classes=["messages-container"]):
                chatbot = gr.Chatbot(
                    elem_classes=["gr-chatbot"],
                    show_label=False,
                    container=False,
                    bubble_full_width=False,
                    show_copy_button=False,
                    avatar_images=None
                )
            
            # Input section with rounded input and embedded send button
            with gr.Column(elem_classes=["input-section"]):
                with gr.Column(elem_classes=["input-wrapper"]):
                    msg = gr.Textbox(
                        placeholder="Message Aesthetic AI...",
                        show_label=False,
                        container=False,
                        lines=1,
                        max_lines=6
                    )
                    send = gr.Button("↑", elem_classes=["send-btn"])

    # Event handlers with smooth message handling
    def submit_message(message, history):
        if not message.strip():
            return history, message
        return chatbot_response(message, history)

    msg.submit(submit_message, [msg, chatbot], [chatbot, msg])
    send.click(submit_message, [msg, chatbot], [chatbot, msg])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
        show_error=True,
        quiet=True
    )