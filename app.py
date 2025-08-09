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
    chat_display = []
    for msg in history:
        lines = msg["content"].split("\n")
        for line in lines:
            if line.strip():
                if msg["role"] == "user":
                    chat_display.append((line, None))
                else:
                    chat_display.append((None, line))
    return chat_display, gr.update(value=""), history

with gr.Blocks(
    css="""
        @import ur[](https://fonts.googleapis.com/css?family=Montserrat);
        * {
            margin: 0;
            padding: 0;
            font-family: "Montserrat", sans-serif;
        }
        body {
            background: #000000;
            height: 100vh;
            width: 100%;
            display: flex;
            padding-top: 1rem;
            color: #fff;
        }
        .gr-block {
            max-width: 400px;
            margin: 0 auto;
            border-radius: 0;
            background: #000000;
            box-shadow: none;
            padding: 0;
            width: 100%;
        }
        .gr-chatbot {
            background: transparent;
            border: none;
            height: 80vh;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: #262626 #000000;
            padding: 0.5rem 0;
        }
        .gr-chatbot .wrap {
            margin: 0 0.5rem;
        }
        .gr-chatbot .wrap.user {
            display: flex;
            justify-content: flex-end;
            flex-direction: row-reverse;
        }
        .gr-chatbot .wrap.bot {
            display: flex;
            align-items: flex-end;
            position: relative;
            padding-left: 2.5rem;
        }
        .gr-chatbot .wrap.bot::before {
            content: "";
            position: absolute;
            left: 0;
            bottom: 0;
            height: 2rem;
            width: 2rem;
            background-image: url('https://avataaars.io/?avatarStyle=Circle&topType=LongHairStraight&accessoriesType=Blank&hairColor=BrownDark&facialHairType=Blank&clotheType=BlazerShirt&eyeType=Default&eyebrowType=Default&mouthType=Default&skinColor=Light');
            background-size: cover;
            border-radius: 50%;
            display: none;
        }
        .gr-chatbot .wrap.bot:has(+ .wrap.user)::before,
        .gr-chatbot .wrap.bot:last-child::before {
            display: block;
        }
        .gr-chatbot .message {
            height: fit-content;
            width: fit-content;
            max-width: 10rem;
            padding: 0.5rem 1rem;
            margin: 0.12rem 0;
            white-space: normal;
            word-wrap: break-word;
            display: inline-block;
        }
        .gr-chatbot .message.bot {
            background: #262626;
            color: #fff;
            border-radius: 0.5rem;
        }
        /* Bot first in group */
        .gr-chatbot .wrap.user + .wrap.bot .message.bot,
        .gr-chatbot > .wrap.bot:first-child .message.bot {
            border-radius: 1rem 0.5rem 0.2rem 0.5rem;
        }
        /* Bot last in group */
        .gr-chatbot .wrap.bot:has(+ .wrap.user) .message.bot,
        .gr-chatbot .wrap.bot:last-child .message.bot {
            border-radius: 0.5rem 0.2rem 0.5rem 1rem;
        }
        .gr-chatbot .message.user {
            background: linear-gradient(180deg, rgba(139,47,184,1) 0%, rgba(103,88,205,1) 51%, rgba(89,116,219,1) 92%);
            color: #fff;
            border-radius: 0.5rem 0.2rem 0.2rem 0.5rem;
        }
        /* User first in group */
        .gr-chatbot .wrap.bot + .wrap.user .message.user,
        .gr-chatbot > .wrap.user:first-child .message.user {
            border-radius: 0.5rem 1rem 0.2rem 0.5rem;
        }
        /* User last in group */
        .gr-chatbot .wrap.user:has(+ .wrap.bot) .message.user,
        .gr-chatbot .wrap.user:last-child .message.user {
            border-radius: 0.5rem 0.2rem 1rem 0.5rem;
        }
        .gr-textbox {
            background: #262626;
            border: none;
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
            color: #fff;
            font-size: 14px;
            height: auto;
        }
        .gr-textbox:focus {
            box-shadow: none;
        }
        .gr-textbox::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        .gr-button {
            background: linear-gradient(180deg, rgba(139,47,184,1) 0%, rgba(103,88,205,1) 51%, rgba(89,116,219,1) 92%);
            color: #fff;
            border: none;
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
            font-weight: normal;
            height: auto;
        }
        .gr-button:hover {
            opacity: 0.9;
        }
        h1 {
            display: none;
        }
        .gr-row {
            align-items: center;
            background: #000000;
            padding: 0.5rem;
            margin: 0;
        }
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #000000;
            border-radius: 8px;
        }
        ::-webkit-scrollbar-thumb {
            background: #262626;
            border-radius: 8px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #333333;
        }
    """
) as demo:
    # gr.Markdown("# ✨ Aesthetic AI Chatbot ✨")  # Commented out to match example
    chatbot_ui = gr.Chatbot(elem_classes=["gr-chatbot"])
    with gr.Row():
        user_input = gr.Textbox(placeholder="Type here...", show_label=False, scale=4, lines=3)
        submit_btn = gr.Button("Send", scale=1)
    state = gr.State([])

    user_input.submit(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, user_input, state])
    submit_btn.click(chatbot, inputs=[user_input, state], outputs=[chatbot_ui, user_input, state])

demo.launch()