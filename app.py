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
        /* 2025 Gen Z-inspired aesthetic: bold colors, neumorphic elements, futuristic vibes */
        body {
            background: linear-gradient(135deg, #1e1e2f 0%, #2a2a4a 100%);
            font-family: 'Inter', sans-serif;
            color: #ffffff;
        }
        .gr-block {
            max-width: 800px;
            margin: 20px auto;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            padding: 20px;
        }
        .gr-chatbot {
            background: transparent;
            border: none;
            height: 500px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: #ff6bcb #2a2a4a;
        }
        .gr-chatbot .message {
            margin: 10px 0;
            padding: 12px 18px;
            border-radius: 15px;
            max-width: 80%;
            transition: transform 0.2s ease;
        }
        .gr-chatbot .message.user {
            background: linear-gradient(45deg, #ff6bcb, #ffb3d9);
            color: #1e1e2f;
            margin-left: auto;
            box-shadow: 0 4px 15px rgba(255, 107, 203, 0.3);
        }
        .gr-chatbot .message.bot {
            background: linear-gradient(45deg, #00f2fe, #4facfe);
            color: #1e1e2f;
            margin-right: auto;
            box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3);
        }
        .gr-textbox {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 12px;
            color: #ffffff;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .gr-textbox:focus {
            border-color: #ff6bcb;
            box-shadow: 0 0 10px rgba(255, 107, 203, 0.5);
            background: rgba(255, 255, 255, 0.15);
        }
        .gr-textbox::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        .gr-button {
            background: linear-gradient(45deg, #ff6bcb, #ffb3d9);
            color: #1e1e2f;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            font-weight: 600;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .gr-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(255, 107, 203, 0.4);
        }
        h1 {
            font-size: 28px;
            text-align: center;
            background: linear-gradient(45deg, #ff6bcb, #00f2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }
        /* Custom scrollbar for modern look */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #2a2a4a;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #ff6bcb;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #ffb3d9;
        }
    """
) as demo:
    gr.Markdown("# ✨ Vibey AI Chatbot ✨")
    chatbot_ui = gr.Chatbot(elem_classes=["gr-chatbot"])
    user_input = gr.Textbox(placeholder="Drop your message here, bestie! 👾", show_label=False)
    state = gr.State([])

    user_input.submit(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, state])

demo.launch()