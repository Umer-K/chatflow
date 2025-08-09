import gradio as gr
import os
import requests

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
    }
    resp = requests.post(API_URL, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

with gr.Blocks(css=".gradio-container {font-family: sans-serif;}") as demo:
    gr.Markdown("# 💬 General Talk Assistant\nFirm & honest GPT-3.5-Turbo chatbot with persistent chat (local browser).")

    with gr.Row():
        with gr.Column(scale=2):
            chatbox = gr.Chatbot([], elem_id="chatbot", height=500, type="messages")
            msg = gr.Textbox(placeholder="Type a message...", show_label=False)
            clear_btn = gr.Button("🗑 Delete Chat")

        with gr.Column(scale=1):
            temperature_slider = gr.Slider(0, 1, value=0.7, step=0.1, label="Temperature")
            token_slider = gr.Slider(50, 2000, value=500, step=50, label="Max Tokens")

    state = gr.State([])

    def respond(user_message, history, temperature, max_tokens):
        history = history or []
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        messages.append({"role": "user", "content": user_message})

        bot_reply = chat_with_gpt(messages, temperature, max_tokens)
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": bot_reply})
        return history, history

    msg.submit(respond, [msg, state, temperature_slider, token_slider], [chatbox, state])
    clear_btn.click(lambda: ([], []), None, [chatbox, state])

    # LocalStorage script injection
    gr.HTML("""
    <script>
    function loadChat() {
        let saved = localStorage.getItem("chat_history");
        if (saved) {
            try {
                let history = JSON.parse(saved);
                let chatEl = gradioApp().querySelector('#chatbot').__gradio_component__;
                chatEl.update(history);
                chatEl.props.value = history;
            } catch(e) { console.error(e); }
        }
    }
    function saveChat() {
        let chatEl = gradioApp().querySelector('#chatbot').__gradio_component__;
        localStorage.setItem("chat_history", JSON.stringify(chatEl.props.value));
    }
    // Load chat on page ready
    setTimeout(loadChat, 500);
    // Observe changes to save
    const obs = new MutationObserver(saveChat);
    setTimeout(() => {
        let target = gradioApp().querySelector('#chatbot');
        if (target) obs.observe(target, {childList: true, subtree: true});
    }, 1000);
    </script>
    """)

demo.launch()
