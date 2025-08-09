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
    history.append({"role": "user", "content": user_message})
    bot_reply = query_openrouter(history)
    history.append({"role": "assistant", "content": bot_reply})
    chat_pairs = [(history[i]["content"], history[i+1]["content"]) for i in range(0, len(history)-1, 2)]
    return chat_pairs, history

with gr.Blocks(
    css="""
        /* 2025 Gen Z-inspired aesthetic: creme color palette, clean spacing, modern vibes */
        body {
            background: linear-gradient(135deg, #f5e9dd 0%, #e8d8c4 100%);
            font-family: 'Inter', sans-serif;
            color: #3c2f2f;
        }
        .gr-block {
            max-width: 800px;
            margin: 40px auto;
            border-radius: 20px;
            background: rgba(255, 245, 230, 0.9);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(60, 47, 47, 0.1);
            padding: 30px;
        }
        .gr-chatbot {
            background: transparent;
            border: none;
            height: 500px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: #d4a373 #f5e9dd;
        }
        .gr-chatbot .message {
            margin: 20px 10px; /* Increased margin for better spacing */
            padding: 15px 20px; /* Increased padding for better text flow */
            border-radius: 15px;
            max-width: 75%;
            line-height: 1.6; /* Improved line height for readability */
            white-space: pre-wrap; /* Ensure text wraps correctly */
            transition: transform 0.2s ease;
        }
        .gr-chatbot .message.user {
            background: linear-gradient(45deg, #d4a373, #e8c39e);
            color: #3c2f2f;
            margin-left: auto;
            box-shadow: 0 4px 15px rgba(212, 163, 115, 0.3);
        }
        .gr-chatbot .message.bot {
            background: linear-gradient(45deg, #a8dadc, #c9e4de);
            color: #3c2f2f;
            margin-right: auto;
            box-shadow: 0 4px 15px rgba(168, 218, 220, 0.3);
        }
        .gr-textbox {
            background: rgba(255, 245, 230, 0.7);
            border: 1px solid rgba(60, 47, 47, 0.2);
            border-radius: 12px;
            padding: 15px;
            color: #3c2f2f;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .gr-textbox:focus {
            border-color: #d4a373;
            box-shadow: 0 0 10px rgba(212, 163, 115, 0.5);
            background: rgba(255, 245, 230, 0.9);
        }
        .gr-textbox::placeholder {
            color: rgba(60, 47, 47, 0.5);
        }
        .gr-button {
            background: linear-gradient(45deg, #d4a373, #e8c39e);
            color: #3c2f2f;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-weight: 600;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .gr-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(212, 163, 115, 0.4);
        }
        h1 {
            font-size: 30px;
            text-align: center;
            background: linear-gradient(45deg, #d4a373, #a8dadc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 30px;
        }
        /* Custom scrollbar for modern look */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f5e9dd;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #d4a373;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #e8c39e;
        }
    """
) as demo:
    gr.Markdown("# ✨ Aesthetic AI Chatbot ✨")
    chatbot_ui = gr.Chatbot(elem_classes=["gr-chatbot"])
    user_input = gr.Textbox(placeholder="Drop your message here, bestie! 👾", show_label=False)
    state = gr.State([])

    user_input.submit(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, state])

demo.launch()