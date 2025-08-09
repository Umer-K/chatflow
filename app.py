import os
import requests
import gradio as gr

# --- (Your API key and function logic remains the same) ---
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
        # Returning chatbot, "" clears the textbox on empty submission
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
    history.append((message, bot_reply)) # Use tuple for history
    
    # Return updated history and clear the textbox
    return history, ""

# --- (CSS is defined in the next block) ---
css = """
/* Modern 2025 AI Chatbot - CORRECTED CSS */

/* --- General App Styling --- */
.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background-color: #ffffff !important;
    max-width: 800px !important; /* Center the main content */
    margin: auto !important; /* Center the main content */
    height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}

/* Hide Gradio branding footer */
footer {
    display: none !important;
}

/* --- App Header --- */
#chatbot-header {
    padding: 16px 24px !important;
    text-align: center !important;
    border-bottom: 1px solid #e5e7eb !important;
    background: #f9fafb !important;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}
#chatbot-header .prose {
    font-size: 24px !important;
    font-weight: 600 !important;
    color: #111827 !important;
    margin: 0 !important;
}

/* --- Chat Area --- */
#chatbot-container {
    flex: 1 !important;
    padding: 0 !important;
    overflow: hidden !important; /* Hide overflow to let chatbot handle scroll */
}
.gradio-chat {
    height: calc(100vh - 180px) !important; /* Adjust height based on header/footer */
    border: none !important;
    background: transparent !important;
    padding: 24px !important;
}

/* --- Message Bubbles --- */
.gradio-chat .message-bubble {
    margin: 12px 0 !important;
    padding: 12px 18px !important;
    border-radius: 18px !important;
    max-width: 75% !important;
    font-size: 15px !important;
    line-height: 1.5 !important;
    word-wrap: break-word !important;
    animation: slideIn 0.3s ease-out;
}

/* User messages - blue, right aligned */
.gradio-chat .message-bubble.user {
    background: #2563eb !important;
    color: #ffffff !important;
    margin-left: auto !important;
    border-bottom-right-radius: 4px !important;
}

/* Bot messages - gray, left aligned */
.gradio-chat .message-bubble.bot {
    background: #f1f3f4 !important;
    color: #374151 !important;
    margin-right: auto !important;
    border-bottom-left-radius: 4px !important;
    border: 1px solid #e5e7eb !important;
}

/* --- Input Section --- */
#input-container {
    padding: 16px 24px 24px 24px !important;
    background: #ffffff !important;
    border-top: 1px solid #e5e7eb !important;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}
#input-container .form {
    display: flex !important;
    gap: 8px !important;
    align-items: center !important;
}

/* Text input */
#msg-textbox textarea {
    padding: 12px 16px !important;
    border: 1px solid #d1d5db !important;
    border-radius: 24px !important;
    font-size: 15px !important;
    background: #ffffff !important;
    outline: none !important;
    resize: none !important;
    transition: border-color 0.2s ease !important;
    box-shadow: none !important;
}
#msg-textbox textarea:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
}
#msg-textbox textarea::placeholder {
    color: #9ca3af !important;
}

/* Send button */
#send-button {
    min-width: 44px !important;
    width: 44px !important;
    height: 44px !important;
    border-radius: 50% !important;
    background: #2563eb !important;
    border: none !important;
    color: #ffffff !important;
    font-size: 20px !important;
    transition: background-color 0.2s ease !important;
}
#send-button:hover {
    background: #1d4ed8 !important;
}

/* --- Animation --- */
@keyframes slideIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
"""

# Create clean, working interface
with gr.Blocks(css=css, title="💬 Aesthetic AI Chatbot") as demo:
    # We use elem_id for more specific CSS targeting
    with gr.Column():
        with gr.Row(elem_id="chatbot-header"):
            gr.Markdown("# 💬 Aesthetic AI Chatbot")
            
        with gr.Column(elem_id="chatbot-container"):
            chatbot = gr.Chatbot(
                elem_id="chatbot",
                elem_classes=["gradio-chat"], # Use Gradio's class for chatbot specifics
                show_label=False,
                container=False,
                bubble_full_width=False
            )
            
        with gr.Row(elem_id="input-container"):
            msg = gr.Textbox(
                elem_id="msg-textbox",
                placeholder="Message Aesthetic AI...",
                show_label=False,
                container=False,
                lines=1,
                max_lines=4,
                scale=10 # Give more space to the textbox
            )
            send = gr.Button(
                "↑", 
                elem_id="send-button",
                scale=1 # Give less space to the button
            )

    # Connect events
    msg.submit(chatbot_response, [msg, chatbot], [chatbot, msg])
    send.click(chatbot_response, [msg, chatbot], [chatbot, msg])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
        show_error=True
    )