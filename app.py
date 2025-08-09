import os
import requests
import gradio as gr

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-3.5-turbo"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

def query_openrouter(messages):
    payload = {"model": MODEL, "messages": messages}
    response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

CUSTOM_CSS = """
.user-msg {
    background-color: #DCF8C6;
    color: #000;
    padding: 8px 12px;
    border-radius: 15px 15px 0 15px;
    max-width: 70%;
    margin-left: auto;
    margin-bottom: 5px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.bot-msg {
    background-color: #F1F0F0;
    color: #333;
    padding: 8px 12px;
    border-radius: 15px 15px 15px 0;
    max-width: 70%;
    margin-right: auto;
    margin-bottom: 5px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
@media (max-width: 600px) {
  .user-msg, .bot-msg {
    max-width: 90% !important;
    font-size: 14px !important;
    padding: 10px !important;
  }
}
body {
    background-color: #f9f9f9;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
#logo {
    display: block;
    margin: 20px auto;
    max-width: 150px;
}
"""

def format_user_message(msg):
    return f'<div class="user-msg">{msg}</div>'

def format_bot_message(msg):
    return f'<div class="bot-msg">{msg}</div>'

def chatbot(user_message, history):
    if history is None:
        history = []

    history.append({"role": "user", "content": format_user_message(user_message)})
    # Strip HTML before sending to API because OpenRouter expects plain text
    api_messages = [{"role": m["role"], "content": strip_html(m["content"])} for m in history]

    bot_reply = query_openrouter(api_messages)
    history.append({"role": "assistant", "content": format_bot_message(bot_reply)})

    chat_pairs = [(history[i]["content"], history[i+1]["content"]) for i in range(0, len(history)-1, 2)]
    return chat_pairs, history

def strip_html(html_str):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_str)

with gr.Blocks(css=CUSTOM_CSS) as demo:
    gr.Image("https://i.imgur.com/4AiXzf8.jpeg", elem_id="logo")  # example logo
    gr.Markdown("<h2 style='text-align:center;'>OpenRouter GPT-3.5 Chatbot</h2>")
    chatbot_ui = gr.Chatbot()
    user_input = gr.Textbox(placeholder="Type your message here...", show_label=False)
    state = gr.State([])

    user_input.submit(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, state])

demo.launch()
