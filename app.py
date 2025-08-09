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
            background: linear-gradient(135deg, #fffaf4 0%, #f8ece0 100%);
            font-family: 'Inter', sans-serif;
            color: #4a4035;
        }
        .gr-block {
            max-width: 800px;
            margin: 50px auto;
            border-radius: 25px;
            background: rgba(255, 250, 244, 0.95);
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(74, 64, 53, 0.1);
            padding: 40px;
        }
        .gr-chatbot {
            background: transparent;
            border: none;
            height: 600px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: #d9b99b #fffaf4;
        }
        .gr-chatbot .message {
            margin: 25px 15px; /* Increased margin for better spacing */
            padding: 20px 25px; /* Increased padding for better text flow */
            border-radius: 18px;
            max-width: 70%;
            line-height: 1.8; /* Improved line height for readability */
            white-space: normal; /* Ensure text wraps naturally */
            transition: transform 0.2s ease;
            word-wrap: break-word; /* Prevent text overflow */
        }
        .gr-chatbot .message.user {
            background: linear-gradient(45deg, #d9b99b, #e8d4c0);
            color: #4a4035;
            margin-left: auto;
            box-shadow: 0 6px 20px rgba(217, 185, 155, 0.3);
        }
        .gr-chatbot .message.bot {
            background: linear-gradient(45deg, #b8d8d8, #d1e8e8);
            color: #4a4035;
            margin-right: auto;
            box-shadow: 0 6px 20px rgba(184, 216, 216, 0.3);
        }
        .gr-textbox {
            background: rgba(255, 250, 244, 0.8);
            border: 2px solid rgba(74, 64, 53, 0.2);
            border-radius: 15px;
            padding: 18px;
            color: #4a4035;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .gr-textbox:focus {
            border-color: #d9b99b;
            box-shadow: 0 0 12px rgba(217, 185, 155, 0.5);
            background: rgba(255, 250, 244, 0.95);
        }
        .gr-textbox::placeholder {
            color: rgba(74, 64, 53, 0.5);
        }
        .gr-button {
            background: linear-gradient(45deg, #d9b99b, #e8d4c0);
            color: #4a4035;
            border: none;
            border-radius: 15px;
            padding: 14px 28px;
            font-weight: 600;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .gr-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(217, 185, 155, 0.4);
        }
        h1 {
            font-size: 32px;
            text-align: center;
            background: linear-gradient(45deg, #d9b99b, #b8d8d8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 35px;
        }
        /* Custom scrollbar for modern look */
        ::-webkit-scrollbar {
            width: 10px;
        }
        ::-webkit-scrollbar-track {
            background: #fffaf4;
            border-radius: 12px;
        }
        ::-webkit-scrollbar-thumb {
            background: #d9b99b;
            border-radius: 12px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #e8d4c0;
        }
    """
) as demo:
    gr.Markdown("# ✨ Aesthetic AI Chatbot ✨")
    chatbot_ui = gr.Chatbot(elem_classes=["gr-chatbot"])
    user_input = gr.Textbox(placeholder="Drop your message here, bestie! 👾", show_label=False)
    state = gr.State([])

    user_input.submit(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, state])

demo.launch()