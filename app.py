import gradio as gr
import os
import requests
import json

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = "You are a firm and honest AI assistant. Speak truthfully, avoid sugar-coating, and provide clear, thoughtful answers."

def chat_with_gpt(messages, temperature=0.7, max_tokens=500):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    resp = requests.post(API_URL, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

# Gradio app
with gr.Blocks(css=".gradio-container {font-family: sans-serif;}") as demo:
    gr.Markdown("# 💬 General Talk Assistant\nFirm & honest GPT-3.5-Turbo chatbot with persistent chat (local browser).")

    with gr.Row():
        with gr.Column(scale=2):
            chatbox = gr.Chatbot([], elem_id="chatbot", height=500)
            msg = gr.Textbox(placeholder="Type a message...", show_label=False)
            clear_btn = gr.Button("🗑 Delete Chat")

        with gr.Column(scale=1):
            temperature_slider = gr.Slider(0, 1, value=0.7, step=0.1, label="Temperature")
            token_slider = gr.Slider(50, 2000, value=500, step=50, label="Max Tokens")

    state = gr.State([])  # Stores messages in memory

    def respond(user_message, history, temperature, max_tokens):
        history = history or []
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for human, ai in history:
            messages.append({"role": "user", "content": human})
            messages.append({"role": "assistant", "content": ai})
        messages.append({"role": "user", "content": user_message})

        bot_reply = chat_with_gpt(messages, temperature, max_tokens)
        history.append((user_message, bot_reply))
        return history, history

    msg.submit(respond, [msg, state, temperature_slider, token_slider], [chatbox, state])
    clear_btn.click(lambda: ([], []), None, [chatbox, state])

# Inject localStorage logic
demo.load(None, None, None, _js="""
() => {
    let saved = localStorage.getItem("chat_history");
    if (saved) {
        try {
            let history = JSON.parse(saved);
            window.gradio_config.components.find(c => c.props.label==="Temperature").props.value;
            // Populate the Chatbot
            gradioApp().querySelector('#chatbot').__gradio_component__.update(history);
        } catch(e) { console.error(e); }
    }

    // Intercept Chatbot updates to save
    const observer = new MutationObserver(() => {
        let chatbotData = gradioApp().querySelector('#chatbot').__gradio_component__.props.value;
        localStorage.setItem("chat_history", JSON.stringify(chatbotData));
    });
    observer.observe(gradioApp().querySelector('#chatbot'), {childList: true, subtree: true});
}
""")

demo.launch()
