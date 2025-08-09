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
    return chat_pairs, gr.update(value=""), history  # Clear textbox after submission

with gr.Blocks(
    css="""
        /* 2025 Gen Z-inspired aesthetic: creme palette, standard chat layout */
        body {
            background: linear-gradient(135deg, #fffaf4 0%, #f8ece0 100%);
            font-family: 'Inter', sans-serif;
            color: #4a4035;
        }
        .gr-block {
            max-width: 800px;
            margin: 30px auto;
            border-radius: 20px;
            background: rgba(255, 250, 244, 0.95);
            backdrop-filter: blur(8px);
            box-shadow: 0 8px 20px rgba(74, 64, 53, 0.1);
            padding: 25px;
        }
        .gr-chatbot {
            background: transparent;
            border: none;
            height: 500px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: #d9b99b #fffaf4;
            padding: 10px 0;
        }
        .gr-chatbot .message {
            margin: 10px 20px;
            padding: 10px 20px;
            border-radius: 15px;
            max-width: 70%;
            min-height: 30px;
            line-height: 1.6;
            white-space: normal;
            word-wrap: break-word;
            transition: transform 0.2s ease;
            display: inline-block;
        }
        .gr-chatbot .message.user {
            background: linear-gradient(45deg, #d9b99b, #e8d4c0);
            color: #4a4035;
            margin-left: auto;
            box-shadow: 0 4px 15px rgba(217, 185, 155, 0.3);
        }
        .gr-chatbot .message.bot {
            background: linear-gradient(45deg, #b8d8d8, #d1e8e8);
            color: #4a4035;
            margin-right: auto;
            box-shadow: 0 4px 15px rgba(184, 216, 216, 0.3);
        }
        .gr-textbox {
            background: rgba(255, 250, 244, 0.8);
            border: 2px solid rgba(74, 64, 53, 0.2);
            border-radius: 20px;
            padding: 10px 15px;
            color: #4a4035;
            font-size: 16px;
            width: 70%; /* Match chatbox width */
            height: 40px; /* Standard height */
            margin: 10px 0;
            transition: all 0.3s ease;
            display: inline-block;
            vertical-align: middle;
        }
        .gr-textbox:focus {
            border-color: #d9b99b;
            box-shadow: 0 0 10px rgba(217, 185, 155, 0.5);
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
            padding: 10px 20px;
            font-weight: 600;
            height: 40px; /* Match textbox height */
            vertical-align: middle;
            margin-left: 10px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .gr-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(217, 185, 155, 0.4);
        }
        h1 {
            font-size: 28px;
            text-align: center;
            background: linear-gradient(45deg, #d9b99b, #b8d8d8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #fffaf4;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #d9b99b;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #e8d4c0;
        }
    """
) as demo:
    gr.Markdown("# ✨ Aesthetic AI Chatbot ✨")
    chatbot_ui = gr.Chatbot(elem_classes=["gr-chatbot"])
    user_input = gr.Textbox(placeholder="Type here...", show_label=False)
    submit_btn = gr.Button("Send", variant="primary")
    state = gr.State([])

    user_input.submit(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, user_input, state])
    submit_btn.click(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, user_input, state])

demo.launch()