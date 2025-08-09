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

def chatbot(user_message, history):
    if history is None:
        history = []
    
    # Add user message to history
    history.append(["", user_message])  # Empty string for user, message for assistant
    
    # Get bot response
    messages = []
    for pair in history:
        if pair[1]:  # User message
            messages.append({"role": "user", "content": pair[1]})
        if pair[0]:  # Assistant message
            messages.append({"role": "assistant", "content": pair[0]})
    
    # Add the latest user message
    messages.append({"role": "user", "content": user_message})
    
    bot_reply = query_openrouter(messages)
    
    # Update the last pair with bot response
    history[-1][0] = bot_reply
    
    return history, "", history

with gr.Blocks(
    title="Aesthetic AI Chatbot",
    css="""
        /* Modern aesthetic chat interface */
        .gradio-container {
            background: linear-gradient(135deg, #f8f4f0 0%, #f0e6d8 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
        }
        
        /* Hide default Gradio elements */
        .gr-button-lg, .gr-button-secondary, footer, .gradio-container .prose {
            display: none !important;
        }
        
        /* Main container */
        .main-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* Header styling */
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .header h1 {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #d4a574, #7fb3d1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            letter-spacing: -0.5px;
        }
        
        /* Chat container */
        .chat-container {
            flex: 1;
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        /* Chatbot styling */
        .gr-chatbot {
            flex: 1;
            border: none !important;
            background: transparent !important;
            padding: 20px !important;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        /* Message bubbles */
        .gr-chatbot .message-wrap {
            display: flex;
            width: 100%;
        }
        
        .gr-chatbot .message-wrap:nth-child(odd) {
            justify-content: flex-start; /* Bot messages */
        }
        
        .gr-chatbot .message-wrap:nth-child(even) {
            justify-content: flex-end; /* User messages */
        }
        
        .gr-chatbot .message {
            max-width: 75%;
            padding: 12px 18px;
            border-radius: 20px;
            font-size: 15px;
            line-height: 1.5;
            word-wrap: break-word;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            animation: fadeIn 0.3s ease-out;
            white-space: pre-wrap;
        }
        
        /* Bot message styling */
        .gr-chatbot .message-wrap:nth-child(odd) .message {
            background: linear-gradient(135deg, #e8f4fd, #d1e8f5);
            color: #2d3748;
            border-bottom-left-radius: 8px;
        }
        
        /* User message styling */
        .gr-chatbot .message-wrap:nth-child(even) .message {
            background: linear-gradient(135deg, #f5e6d3, #e8d4bf);
            color: #2d3748;
            border-bottom-right-radius: 8px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Input area */
        .input-area {
            padding: 20px;
            background: rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(5px);
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .input-row {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }
        
        /* Text input styling */
        .gr-textbox {
            flex: 1;
            background: rgba(255, 255, 255, 0.9) !important;
            border: 2px solid rgba(212, 165, 116, 0.3) !important;
            border-radius: 20px !important;
            padding: 12px 18px !important;
            font-size: 15px !important;
            color: #2d3748 !important;
            transition: all 0.2s ease !important;
            resize: none !important;
        }
        
        .gr-textbox:focus {
            border-color: #d4a574 !important;
            box-shadow: 0 0 0 3px rgba(212, 165, 116, 0.1) !important;
            background: rgba(255, 255, 255, 1) !important;
        }
        
        .gr-textbox::placeholder {
            color: rgba(45, 55, 72, 0.5) !important;
        }
        
        /* Send button styling */
        .send-button {
            background: linear-gradient(135deg, #d4a574, #c49660) !important;
            color: white !important;
            border: none !important;
            border-radius: 16px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 12px rgba(212, 165, 116, 0.3) !important;
        }
        
        .send-button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(212, 165, 116, 0.4) !important;
            background: linear-gradient(135deg, #c49660, #b8865a) !important;
        }
        
        .send-button:active {
            transform: translateY(0) !important;
        }
        
        /* Custom scrollbar */
        .gr-chatbot::-webkit-scrollbar {
            width: 6px;
        }
        
        .gr-chatbot::-webkit-scrollbar-track {
            background: rgba(212, 165, 116, 0.1);
            border-radius: 3px;
        }
        
        .gr-chatbot::-webkit-scrollbar-thumb {
            background: rgba(212, 165, 116, 0.4);
            border-radius: 3px;
        }
        
        .gr-chatbot::-webkit-scrollbar-thumb:hover {
            background: rgba(212, 165, 116, 0.6);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main-container {
                padding: 10px;
            }
            
            .gr-chatbot .message {
                max-width: 85%;
                font-size: 14px;
                padding: 10px 14px;
            }
            
            .header h1 {
                font-size: 24px;
            }
        }
        
        /* Hide Gradio branding and unnecessary elements */
        .gr-interface > div:first-child, 
        .gradio-container .gr-button-lg,
        .gr-form > div:last-child,
        .share-button,
        .gr-block.gr-box > div:last-child {
            display: none !important;
        }
    """
) as demo:
    
    with gr.Column(elem_classes=["main-container"]):
        # Header
        with gr.Column(elem_classes=["header"]):
            gr.Markdown("# ✨ Aesthetic AI Chatbot ✨")
        
        # Chat area
        with gr.Column(elem_classes=["chat-container"]):
            chatbot_ui = gr.Chatbot(
                elem_classes=["gr-chatbot"],
                show_label=False,
                container=False,
                height=500,
                bubble_full_width=False,
                show_copy_button=False
            )
            
            # Input area
            with gr.Column(elem_classes=["input-area"]):
                with gr.Row(elem_classes=["input-row"]):
                    user_input = gr.Textbox(
                        placeholder="Type your message here...",
                        show_label=False,
                        container=False,
                        scale=4,
                        lines=1,
                        max_lines=4
                    )
                    submit_btn = gr.Button(
                        "Send", 
                        variant="primary",
                        scale=1,
                        elem_classes=["send-button"]
                    )

    # State management
    state = gr.State([])

    # Event handlers
    def handle_submit(user_message, history):
        if not user_message.strip():
            return history, "", history
        return chatbot(user_message.strip(), history)

    user_input.submit(
        handle_submit, 
        inputs=[user_input, state], 
        outputs=[chatbot_ui, user_input, state]
    )
    
    submit_btn.click(
        handle_submit, 
        inputs=[user_input, state], 
        outputs=[chatbot_ui, user_input, state]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
        show_error=True,
        quiet=False
    )