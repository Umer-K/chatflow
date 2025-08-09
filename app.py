# app.py
import gradio as gr
import os
import requests
import json

# ---- Config ----
API_URL = "https://openrouter.ai/api/v1/chat/completions"
SYSTEM_PROMPT = "You are a firm and honest AI assistant. Speak truthfully, avoid sugar-coating, and provide clear, thoughtful answers."
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "").strip()

# ---- API Call ----
def chat_with_gpt(messages, temperature=0.7, max_tokens=500):
    if not OPENROUTER_KEY:
        return "[ERROR] Missing API key. Please set OPENROUTER_KEY in Hugging Face Spaces 'Settings → Secrets'."
    
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

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"[API ERROR] {e}"
    except (KeyError, IndexError, json.JSONDecodeError):
        return "[ERROR] Unexpected API response format."

# ---- History to Chatbot format ----
def state_to_chat_pairs(state):
    pairs = []
    i = 0
    while i < len(state):
        if state[i]["role"] == "user":
            user_msg = state[i]["content"]
            assistant_msg = ""
            if i + 1 < len(state) and state[i + 1]["role"] == "assistant":
                assistant_msg = state[i + 1]["content"]
                i += 2
            else:
                i += 1
            pairs.append((user_msg, assistant_msg))
        else:
            i += 1
    return pairs

# ---- Main Respond ----
def respond(user_message, history, temperature, max_tokens):
    history = history or []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    bot_reply = chat_with_gpt(messages, temperature, max_tokens)

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": bot_reply})

    return state_to_chat_pairs(history), history

# ---- UI ----
css = """
body, .gradio-container { background-color: #000 !important; color: #e6eef8 !important; }
#chatbot { border: 1px solid rgba(255,255,255,0.05); }
"""

with gr.Blocks(css=css, theme=gr.themes.Soft()) as demo:
    gr.Markdown("<h1>💬 Nightbot — Firm & Honest</h1>")
    with gr.Row():
        with gr.Column(scale=2):
            chatbox = gr.Chatbot([], elem_id="chatbot", height=520)
            with gr.Row():
                user_input = gr.Textbox(placeholder="Type a message...", lines=2)
                send_btn = gr.Button("Send")
            state = gr.State([])
        with gr.Column(scale=1):
            temperature = gr.Slider(0, 1, value=0.7, step=0.1, label="Temperature")
            max_tokens = gr.Slider(50, 2000, value=500, step=50, label="Max Tokens")
            clear = gr.Button("Clear Chat 🗑️")

    send_btn.click(respond, [user_input, state, temperature, max_tokens], [chatbox, state])
    user_input.submit(respond, [user_input, state, temperature, max_tokens], [chatbox, state])
    clear.click(lambda: ([], []), None, [chatbox, state])

# ---- Run ----
if __name__ == "__main__":
    demo.queue(concurrency_count=5).launch(server_name="0.0.0.0", server_port=7860)
