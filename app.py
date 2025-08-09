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

# Clean, modern CSS
css = """
/* Reset and base styles */
* {
    box-sizing: border-box;
}

.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    min-height: 100vh !important;
}

/* Hide unwanted elements */
footer, .gr-button-lg, .gradio-container > div > div:last-child {
    display: none !important;
}

/* Main layout */
.main-wrap {
    max-width: 1000px !important;
    margin: 0 auto !important;
    padding: 20px !important;
    height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
}

/* Title */
.title-container h1 {
    text-align: center !important;
    color: #2c3e50 !important;
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    margin: 0 0 30px 0 !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1) !important;
}

/* Chat container */
.chat-wrapper {
    flex: 1 !important;
    background: white !important;
    border-radius: 20px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
    padding: 0 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
}

/* Chatbot area */
.gr-chatbot {
    flex: 1 !important;
    border: none !important;
    background: transparent !important;
    padding: 20px !important;
    overflow-y: auto !important;
    max-height: 500px !important;
}

.gr-chatbot > div {
    gap: 15px !important;
}

/* Message styling */
.gr-chatbot .user, .gr-chatbot .bot {
    padding: 12px 18px !important;
    border-radius: 18px !important;
    max-width: 80% !important;
    font-size: 15px !important;
    line-height: 1.4 !important;
    margin: 5px 0 !important;
    word-wrap: break-word !important;
}

.gr-chatbot .user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    margin-left: auto !important;
    border-bottom-right-radius: 5px !important;
}

.gr-chatbot .bot {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
    color: white !important;
    margin-right: auto !important;
    border-bottom-left-radius: 5px !important;
}

/* Input area */
.input-section {
    background: #f8f9fa !important;
    padding: 20px !important;
    border-top: 1px solid #e9ecef !important;
}

.input-row {
    display: flex !important;
    gap: 10px !important;
    align-items: flex-end !important;
}

/* Text input */
.message-input {
    flex: 1 !important;
    padding: 15px 20px !important;
    border: 2px solid #e9ecef !important;
    border-radius: 25px !important;
    font-size: 16px !important;
    background: white !important;
    resize: none !important;
    outline: none !important;
    transition: border-color 0.3s ease !important;
}

.message-input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* Send button - FIXED */
.send-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 15px 30px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    min-width: 100px !important;
    height: 50px !important;
}

.send-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
}

.send-btn:active {
    transform: translateY(0) !important;
    box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3) !important;
}

/* Scrollbar */
.gr-chatbot::-webkit-scrollbar {
    width: 6px;
}

.gr-chatbot::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

.gr-chatbot::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 10px;
}

.gr-chatbot::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

/* Responsive */
@media (max-width: 768px) {
    .main-wrap {
        padding: 10px !important;
    }
    
    .title-container h1 {
        font-size: 2rem !important;
    }
    
    .gr-chatbot .user, .gr-chatbot .bot {
        max-width: 90% !important;
        font-size: 14px !important;
    }
}
"""

# Create interface
with gr.Blocks(css=css, title="Aesthetic AI Chatbot") as demo:
    
    # Title
    with gr.Column(elem_classes=["title-container"]):
        gr.Markdown("# 💬 Aesthetic AI Chatbot")
    
    # Main chat area
    with gr.Column(elem_classes=["chat-wrapper"]):
        chatbot = gr.Chatbot(
            elem_classes=["gr-chatbot"],
            show_label=False,
            container=False,
            bubble_full_width=False
        )
        
        # Input section
        with gr.Column(elem_classes=["input-section"]):
            with gr.Row(elem_classes=["input-row"]):
                msg = gr.Textbox(
                    placeholder="Type your message here...",
                    show_label=False,
                    container=False,
                    scale=4,
                    elem_classes=["message-input"]
                )
                send = gr.Button(
                    "Send",
                    scale=1,
                    elem_classes=["send-btn"],
                    variant="primary"
                )

    # Event handlers
    msg.submit(chatbot_response, [msg, chatbot], [chatbot, msg])
    send.click(chatbot_response, [msg, chatbot], [chatbot, msg])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
        show_error=True
    )