import gradio as gr
import requests
import os

# --- CONFIG ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-3.5-turbo"

# --- CSS from your template with some dark tweaks ---
custom_css = """
*{
  box-sizing:border-box;
}
body{
  margin:0;
  font:.9em/1.5 'Roboto', sans-serif;
  cursor:default;
  background:#121212;
  color:#eee;
}
.box{
  width:80%;
  max-width:600px;
  margin:2em auto;
}
.message{
  width:calc(100% - 100px);
  border-radius:15px;
  padding:1em;
  font-size:1rem;
  line-height:1.4;
  word-wrap: break-word;
}
.person-a .message{
  background:#2c2c2c;
  color:#eee;
}
.person-a{
  display:flex;
  align-items:flex-end;
}
.icon{
  --size:40px;
  width:var(--size);
  height:var(--size);
  background:url(https://i.ibb.co/vB9B6G8/mWDLI93.gif);
  background-position:center;
  background-size:cover;
  border-radius:100%;
  margin-right:.8em;
  position:relative;
  flex-shrink: 0;
}
.icon::after{
  content:' ';
  position:absolute;
  width:10px;
  height:10px;
  background:#00ff00a0;
  border-radius:100%;
  bottom:0;
  right:0;
}
.person-b .message{
  background:#005f9e;
  margin:2em 0;
  margin-left:100px;
  color:#e0eaff;
  text-align:right;
}
.message svg{
  height:26px;
  vertical-align:middle;
}
.last{
  width:auto;
}
"""

# --- HTML wrapper for messages ---
def render_messages(chat_history):
    """
    chat_history: list of (user_msg, bot_msg)
    Returns HTML string rendering all chat messages with your template style.
    """
    html = '<div class="box">'
    # user is person-a, bot is person-b
    for user_msg, bot_msg in chat_history:
        html += f'''
        <div class="person-a">
          <div class="icon"></div>
          <div class="message">{gr.utils.escape_html(user_msg)}</div>
        </div>
        <div class="person-b">
          <div class="message">{gr.utils.escape_html(bot_msg)}</div>
        </div>
        '''
    html += '</div>'
    return html

# --- OpenRouter API call ---
def openrouter_chat(messages):
    """
    messages: List of dict {"role": "user"/"assistant"/"system", "content": "..."}
    Returns assistant reply text.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }
    response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

# --- Gradio functions ---
def respond(user_input, chat_history):
    """
    Append user message, call API, append bot reply, return updated chat_history and rendered html.
    """
    if chat_history is None:
        chat_history = []
    # Add user message
    chat_history.append((user_input, None))

    # Prepare messages for OpenRouter
    messages = []
    for user_m, bot_m in chat_history:
        messages.append({"role": "user", "content": user_m})
        if bot_m:
            messages.append({"role": "assistant", "content": bot_m})

    try:
        bot_reply = openrouter_chat(messages)
    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    # Update last bot reply in chat history
    chat_history[-1] = (user_input, bot_reply)

    # Render HTML
    rendered = render_messages(chat_history)
    return "", chat_history, rendered

def reset_chat():
    return "", [], render_messages([])

# --- Build UI ---
with gr.Blocks(css=custom_css, title="Dark Stylish Chatbot with OpenRouter GPT-3.5") as demo:

    state = gr.State([])  # chat_history as list of tuples

    chat_html = gr.HTML(render_messages([]), elem_id="chatbox")

    with gr.Row():
        user_input = gr.Textbox(show_label=False, placeholder="Type your message and press Enter", lines=2)
        submit_btn = gr.Button("Send")

    submit_btn.click(respond, inputs=[user_input, state], outputs=[user_input, state, chat_html])
    user_input.submit(respond, inputs=[user_input, state], outputs=[user_input, state, chat_html])

    reset_btn = gr.Button("Reset Chat")
    reset_btn.click(reset_chat, inputs=None, outputs=[user_input, state, chat_html])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
