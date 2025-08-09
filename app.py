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

with gr.Blocks() as demo:
    gr.Markdown("# Chatbot powered by OpenRouter GPT-3.5 Turbo")
    chatbot_ui = gr.Chatbot()
    user_input = gr.Textbox(placeholder="Type your message here...", show_label=False)
    state = gr.State([])

    user_input.submit(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, state])

demo.launch()
