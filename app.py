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
    return chat_pairs, gr.update(value=""), history

with gr.Blocks(
    css="""
        /* Optimized Instagram-inspired layout with reduced empty space */
        body {
            background: linear-gradient(135deg, #fffaf4 0%, #f8ece0 100%);
            font-family: 'Inter', sans-serif;
            color: #4a4035;
            margin: 0;
            padding: 0;
        }
        .gr-block {
            max-width: 800px;
            margin: 10px auto;
            border-radius: 15px;
            background: rgba(255, 250, 244, 0.95);
            backdrop-filter: blur(5px);
            box-shadow: 0 5px 15px rgba(74, 64, 53, 0.1);
            padding: 10px;
        }
        .gr-chatbot {
            background: transparent;
            border: none;
            height: 80vh;
            min-height: 400px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: #d9b99b #fffaf4;
            padding: 5px 0;
        }
        .gr-chatbot .message {
            margin: 10px 10px;
            padding: 8px 15px;
            border-radius: 10px;
            max-width: 70%; /* Wider bubbles to fill space */
            min-height: 40px;
            line-height: 1.4;
            white-space: normal;
            word-wrap: break-word;
            transition: transform 0.2s ease;
            display: inline-block;
        }
        .gr-chatbot .message.user {
            background: linear-gradient(45deg, #d9b99b, #e8d4c0);
            color: #4a4035;
            margin-left: auto;
            margin-right: 10px;
            box-shadow: 0 3px 10px rgba(217, 185, 155, 0.2);
        }
        .gr-chatbot .message.bot {
            background: linear-gradient(45deg, #b8d8d8, #d1e8e8);
            color: #4a4035;
            margin-right: auto;
            margin-left: 10px;
            box-shadow: 0 3px 10px rgba(184, 216, 216, 0.2);
        }
        .gr-textbox {
            background: rgba(255, 250, 244, 0.8);
            border: 2px solid rgba(74, 64, 53, 0.2);
            border-radius: 20px;
            padding: 8px 12px;
            color: #4a4035;
            font-size: 14px;
            height: 35px;
            transition: all 0.3s ease;
        }
        .gr-textbox:focus {
            border-color: #d9b99b;
            box-shadow: 0 0 8px rgba(217, 185, 155, 0.4);
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
            padding: 8px 15px;
            font-weight: 600;
            height: 35px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .gr-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 3px 10px rgba(217, 185, 155, 0.3);
        }
        h1 {
            font-size: 24px;
            text-align: center;
            background: linear-gradient(45deg, #d9b99b, #b8d8d8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 5px 0;
        }
        .gr-row {
            align-items: center;
        }
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #fffaf4;
            border-radius: 8px;
        }
        ::-webkit-scrollbar-thumb {
            background: #d9b99b;
            border-radius: 8px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #e8d4c0;
        }
    """
) as demo:
    gr.Markdown("# ✨ Aesthetic AI Chatbot ✨")
    chatbot_ui = gr.Chatbot(elem_classes=["gr-chatbot"])
    with gr.Row():
        user_input = gr.Textbox(placeholder="Type here...", show_label=False, scale=4)
        submit_btn = gr.Button("Send", variant="primary", scale=1)
    state = gr.State([])

    user_input.submit(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, user_input, state])
    submit_btn.click(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, user_input, state])

demo.launch()