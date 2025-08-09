# app.py
import gradio as gr
import os
import requests

# ---- Config ----
API_URL = "https://openrouter.ai/api/v1/chat/completions"
SYSTEM_PROMPT = "You are a firm and honest AI assistant. Speak truthfully, avoid sugar-coating, and provide clear, thoughtful answers."
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "").strip()

# ---- API Call ----
def chat_with_gpt(messages, temperature=0.7, max_tokens=500):
    if not OPENROUTER_KEY:
        return "[ERROR] Missing API key. Please set OPENROUTER_KEY in Hugging Face Spaces → Settings → Secrets."
    try:
        resp = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=60
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[API ERROR] {str(e)}"

# ---- Main Respond ----
def respond(user_message, history, temperature, max_tokens):
    history = history or []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    messages.append({"role": "user", "content": user_message})

    bot_reply = chat_with_gpt(messages, temperature, max_tokens)

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": bot_reply})
    return history, history

# ---- Custom Dark Theme CSS ----
dark_css = """
body, .gradio-container {
    background-color: #000 !important;
    color: #e6eef8 !important;
    font-family: 'Segoe UI', sans-serif;
}
#chatbot {
    background: rgba(20,20,20,0.8) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    padding: 10px !important;
    animation: fadeIn 0.4s ease-in-out;
}
.message {
    transition: all 0.3s ease-in-out;
}
.message.user {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364) !important;
    color: #fff !important;
}
.message.assistant {
    background: rgba(255,255,255,0.05) !important;
    color: #e6eef8 !important;
}
#typing {
    font-style: italic;
    opacity: 0.8;
    animation: pulse 1.2s infinite;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
"""

# ---- Build UI ----
with gr.Blocks(css=dark_css) as demo:
    gr.Markdown("<h1 style='color:white;'>💬 Nightbot — Firm & Honest</h1>")

    with gr.Row():
        with gr.Column(scale=2):
            chatbox = gr.Chatbot([], elem_id="chatbot", height=520, type='messages')
            with gr.Row():
                msg = gr.Textbox(placeholder="Type your message...", show_label=False, scale=4)
                send_btn = gr.Button("Send", scale=1)
            clear_btn = gr.Button("🗑 Clear Chat")

        with gr.Column(scale=1):
            temperature_slider = gr.Slider(0, 1, value=0.7, step=0.1, label="Temperature")
            token_slider = gr.Slider(50, 2000, value=500, step=50, label="Max Tokens")

    state = gr.State([])

    send_btn.click(respond, [msg, state, temperature_slider, token_slider], [chatbox, state])
    msg.submit(respond, [msg, state, temperature_slider, token_slider], [chatbox, state])
    clear_btn.click(lambda: ([], []), None, [chatbox, state])

    # ---- LocalStorage + Typing Animation ----
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
        if (chatEl && chatEl.props && chatEl.props.value) {
            localStorage.setItem("chat_history", JSON.stringify(chatEl.props.value));
        }
    }
    function showTyping() {
        let chatEl = document.querySelector('#chatbot');
        if (chatEl) {
            let typingEl = document.createElement('div');
            typingEl.id = 'typing';
            typingEl.innerText = 'Assistant is typing...';
            chatEl.appendChild(typingEl);
        }
    }
    function hideTyping() {
        let typingEl = document.getElementById('typing');
        if (typingEl) typingEl.remove();
    }
    setTimeout(loadChat, 500);
    const obs = new MutationObserver(saveChat);
    setTimeout(() => {
        let target = gradioApp().querySelector('#chatbot');
        if (target) obs.observe(target, {childList: true, subtree: true});
    }, 1000);
    </script>
    """)

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
