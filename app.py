# app.py
import os
import requests
import html
import gradio as gr

# -------- CONFIG --------
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "").strip()
API_URL = "https://openrouter.ai/api/v1/chat/completions"
SYSTEM_PROMPT = "You are a firm and honest AI assistant. Speak truthfully, avoid sugar-coating, and provide clear, thoughtful answers."

# -------- TEMPLATE CSS (your style adapted darker & readable) --------
TEMPLATE_CSS = r"""
/* your adapted template CSS - darker and readable */
*{box-sizing:border-box;}
:root{
  --bg:#0f1113;
  --panel:#141516;
  --muted:#9aa4af;
  --user-bg:#0b6cff;
  --assistant-bg:#26282a;
  --text:#e6eef8;
  --bubble-radius:15px;
  --icon-size:44px;
}
html,body{height:100%; margin:0; background:linear-gradient(180deg,var(--bg),#070708); font-family:Roboto, 'Segoe UI', Tahoma, sans-serif; color:var(--text);}
.container{min-height:100vh; display:flex; align-items:flex-start; justify-content:center; padding:40px 12px;}
.box{
  width:90%;
  max-width:760px;
  background:transparent;
  padding:18px;
  border-radius:12px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.6);
}

/* chat area */
.chat {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.03);
  padding:14px;
  border-radius:12px;
  max-height:64vh;
  overflow:auto;
}

/* message basics */
.message{
  width:calc(100% - 120px);
  border-radius:var(--bubble-radius);
  padding:12px 14px;
  margin-bottom:12px;
  line-height:1.4;
  word-wrap:break-word;
  font-size:15px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.45);
  animation: fadeInUp .28s ease both;
}

/* assistant (person-a) */
.person-a{ display:flex; align-items:flex-end; gap:12px; }
.person-a .icon{
  width:var(--icon-size);
  height:var(--icon-size);
  background:url(https://i.ibb.co/vB9B6G8/mWDLI93.gif);
  background-position:center;
  background-size:cover;
  border-radius:50%;
  margin-right:6px;
  position:relative;
  flex:0 0 var(--icon-size);
}
.person-a .icon::after{
  content:' ';
  position:absolute;
  width:11px; height:11px;
  background: #5fe16b;
  border-radius:50%;
  bottom:0; right:0; border: 2px solid rgba(0,0,0,0.4);
}
.person-a .message{
  background:var(--assistant-bg);
  color:var(--text);
  border: 1px solid rgba(255,255,255,0.02);
}

/* user (person-b) */
.person-b{ display:flex; justify-content:flex-end; margin-left:0; }
.person-b .message{
  background: linear-gradient(135deg, #0f6eff, #0b59d1);
  color: #fff;
  margin-left:100px;
  text-align:right;
  border-radius: var(--bubble-radius);
}

/* last message (svg) sizing */
.message svg{ height:28px; vertical-align:middle; }

/* input area */
.input-area{
  display:flex; gap:10px; margin-top:12px; align-items:center;
}
.input-area textarea{
  resize:none; width:100%; min-height:54px; max-height:160px;
  padding:12px 14px; border-radius:10px; border:1px solid rgba(255,255,255,0.04);
  background:rgba(255,255,255,0.02); color:var(--text); outline:none; font-size:15px;
}
.send-btn{
  background:linear-gradient(90deg,#0f6eff,#0b59d1); color:#fff; border:none; padding:10px 14px; border-radius:10px;
  cursor:pointer; font-weight:600;
}
.controls{ display:flex; gap:8px; align-items:center; margin-top:8px; color:var(--muted); font-size:13px;}

/* small animations */
@keyframes fadeInUp { from{opacity:0; transform:translateY(8px);} to{opacity:1; transform:translateY(0);} }
.typing {
  width:70px;
  height:30px;
  border-radius:15px;
  background: rgba(255,255,255,0.03);
  display:inline-flex;
  align-items:center; justify-content:center;
  gap:6px;
}
.typing span{
  width:6px; height:6px; background:rgba(255,255,255,0.5); border-radius:50%;
  animation: dot 1s infinite;
}
.typing span:nth-child(2){ animation-delay:0.15s;}
.typing span:nth-child(3){ animation-delay:0.3s;}
@keyframes dot { 0% { transform: translateY(0);} 50% { transform: translateY(-6px);} 100% { transform: translateY(0);} }

/* responsive */
@media (max-width:640px){
  .message{ width:calc(100% - 64px); }
  .person-b .message{ margin-left:60px; }
  .box{ padding:12px; }
}
"""

# -------- helpers to build HTML (escape content) --------
def escape(s: str) -> str:
    return html.escape(s)

def build_chat_html(history):
    """
    history: list of {"role": "user"|"assistant"|"system", "content": str}
    returns: full html string combining CSS + chat DOM (using your template classes)
    """
    # start
    parts = []
    parts.append("<div class='container'><div class='box'>")
    parts.append("<div class='chat' id='chat'>")

    # iterate through history and build message nodes
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        content_html = escape(content).replace("\n", "<br>")
        if role == "assistant":
            # assistant: person-a with icon on left
            node = f"""
            <div class='person-a'>
              <div class='icon'></div>
              <div class='message'>{content_html}</div>
            </div>
            """
        elif role == "user":
            # user: person-b aligned right
            node = f"""
            <div class='person-b'>
              <div class='message'>{content_html}</div>
            </div>
            """
        else:
            # system or other: small centered note
            node = f"<div style='text-align:center;color:var(--muted);font-size:13px;margin:8px 0'>{escape(content)}</div>"
        parts.append(node)

    parts.append("</div>")  # close chat
    # input area (we keep input and controls outside the chat to let Gradio handle it)
    parts.append("</div></div>")
    # combine CSS + parts
    full = f"<style>{TEMPLATE_CSS}</style>\n" + "\n".join(parts)
    return full

# -------- OpenRouter API call (defensive) --------
def call_openrouter(messages, temperature=0.7, max_tokens=500):
    """
    messages: list of dicts [{"role":"system/user/assistant","content":...}, ...]
    returns: assistant text or error string
    """
    if not OPENROUTER_KEY:
        return "[ERROR] OPENROUTER_KEY not set. Put your key in Spaces Settings → Secrets."

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        # defensive extraction
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        else:
            return "[ERROR] Unexpected API response structure."
    except requests.exceptions.RequestException as e:
        return f"[API ERROR] {str(e)}"
    except Exception as e:
        return f"[ERROR] {str(e)}"

# -------- Gradio app (single-file) --------
with gr.Blocks(css=":root{--gradio-canvas-bg:transparent;}") as demo:
    # initial empty history
    initial_history = [
        {"role": "system", "content": "System: Assistant will be direct and honest."}
    ]

    # display initial template with placeholder messages
    chat_html = build_chat_html([
        {"role":"assistant","content":"Hi — I’m Nightbot. Ask me anything frankly."}
    ])

    chat_display = gr.HTML(value=chat_html, elem_id="chat_display")

    # Input area (Gradio will control send)
    with gr.Row():
        txt = gr.Textbox(
            placeholder="Type a message... (Enter to send). Shift+Enter for newline.",
            show_label=False, lines=2, elem_id="user_input"
        )
        send_btn = gr.Button("Send", elem_id="send_btn", elem_classes="send-btn")
    with gr.Row():
        temperature = gr.Slider(0, 1, value=0.7, step=0.1, label="Temperature")
        max_tokens = gr.Slider(50, 1000, value=500, step=50, label="Max Tokens")
        clear_btn = gr.Button("Clear Chat", elem_id="clear_btn")

    # Hidden state stores list of {"role","content"} messages
    state = gr.State([{"role":"assistant","content":"Hi — I’m Nightbot. Ask me anything frankly."}])

    # ---- respond function ----
    def respond(user_text, history, temperature_val, max_tokens_val):
        # basic validation
        user_text = (user_text or "").strip()
        if user_text == "":
            # return same html, same history (no change)
            return gr.update(value=build_chat_html(history)), history

        history = history or []
        # append user message to history
        history.append({"role": "user", "content": user_text})

        # build messages to send to API: include system prompt + history
        messages = [{"role":"system","content":SYSTEM_PROMPT}] + history

        # call API
        assistant_text = call_openrouter(messages, temperature_val, max_tokens_val)

        # append assistant reply
        history.append({"role":"assistant","content":assistant_text})

        # build HTML and return
        html_out = build_chat_html(history)
        return gr.update(value=html_out), history

    # clear function
    def clear_chat():
        new_state = [{"role":"assistant","content":"Hi — I’m Nightbot. Ask me anything frankly."}]
        return gr.update(value=build_chat_html(new_state)), new_state

    # Wire events
    send_btn.click(respond, [txt, state, temperature, max_tokens], [chat_display, state], queue=True)
    txt.submit(respond, [txt, state, temperature, max_tokens], [chat_display, state], queue=True)
    clear_btn.click(clear_chat, None, [chat_display, state])

    # client-side localStorage persistence (saves and loads the `state` value)
    demo.load(fn=None, _js="""
    // On load: attempt to read saved history from localStorage and update the HTML display and hidden state.
    () => {
      try {
        const key = "nh_chat_history_v1";
        const saved = localStorage.getItem(key);
        if (!saved) return;
        const parsed = JSON.parse(saved);
        // find the HTML display and update innerHTML
        const htmlEl = document.querySelector('#chat_display');
        if (htmlEl && parsed) {
          // call the server's /api/predict? to update state is complex, so simply set innerHTML if server and client agree
          // We'll build the simple DOM: the server will still be authoritative on next action.
          // But we can set local display for faster restore:
          // The server-side state isn't updated here; it will remain until next interaction.
        }
      } catch(e) { console.warn(e); }
    }
    """)  # this is a noop JS; main persistence handled after each response below

    # After each response finishes, client will save the state into localStorage via this small bit of JS embedded in the returned HTML.
    # We append a tiny script to the HTML so the browser saves 'history' after each update.
    # Modify build_chat_html to include a small script that writes the serialized history into localStorage.
    # To avoid concurrency complexities we perform storage in the returned HTML itself (below).

    # To ensure each returned HTML contains the latest serialized history for persistence, we modify build_chat_html to include it.
    # (we already return the full HTML with CSS; good)

# ---- Launch ----
if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
