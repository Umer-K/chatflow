import gradio as gr
import requests
import os
import json

# Set your OpenRouter API key as a secret on Hugging Face Spaces
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Custom CSS to replicate the ChatGPT front page and chat UI
# This CSS now includes the subtle background gradient, refined search bar, and updated text sizes.
custom_css = """
/* Body and main container styles */
.gradio-container {
    height: 100vh;
    padding: 0;
    margin: 0;
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
    background-color: #f7f7f8; /* Base light gray background */
    background-image: linear-gradient(to bottom, #ffffff, #f7f7f8); /* Subtle gradient */
}

/* Main chat area container */
.main-chat-area {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
    padding: 0 1rem;
    max-width: 900px;
    margin: 0 auto;
}

/* Chatbot component styling */
#chatbot {
    flex-grow: 1;
    overflow-y: auto;
    width: 100%;
    max-width: 800px;
    margin: 2rem auto; /* Add some top margin for the chat area */
    padding: 1rem;
    border: none !important;
}

/* Hide the chatbot label */
#chatbot label {
    display: none;
}

/* "Introducing GPT-5" text and description */
#welcome-header {
    text-align: center;
    color: #000000;
    font-size: 2.2rem; /* Slightly smaller header */
    font-weight: 500;
    margin-bottom: 0.5rem;
}
#welcome-subtitle {
    text-align: center;
    color: #494949;
    font-size: 1rem;
    font-weight: 400;
    max-width: 600px;
    margin-bottom: 2.5rem; /* Slightly larger bottom margin */
}

/* Input area styling */
.chat-input-area {
    width: 100%;
    position: relative;
    padding: 0;
    margin-top: 1rem;
    max-width: 800px;
}

.input-box {
    width: 100%;
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 1.5rem;
    box-shadow: 0 0 15px rgba(0,0,0,0.08), inset 0 1px 2px rgba(0,0,0,0.02); /* Subtle inner shadow */
    display: flex;
    align-items: center;
    padding: 0.9rem 1.5rem; /* Increased padding */
    transition: box-shadow 0.3s ease;
}
.input-box:focus-within {
    box-shadow: 0 0 15px rgba(0,0,0,0.15), inset 0 1px 2px rgba(0,0,0,0.02);
}

.input-box textarea {
    width: 100%;
    border: none;
    background: transparent;
    color: black;
    font-size: 1rem;
    resize: none;
    outline: none;
    padding: 0.25rem 0;
}

/* Hide the Gradio-default send button text */
.input-box button > span {
    display: none;
}

/* Styling the Send button icon */
.input-box button {
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    margin-left: 0.5rem;
}
.input-box button svg {
    width: 24px;
    height: 24px;
    fill: #9b9b9b;
}

/* Chat message bubbles */
#chatbot .message-wrap.user {
    background-color: #d1e7ff !important; /* A light blue for user messages */
    color: black !important;
    border-radius: 12px;
    padding: 0.7rem 1rem !important; /* Adjust message padding */
    margin: 0.25rem 0;
}

#chatbot .message-wrap.bot {
    background-color: white !important;
    color: black !important;
    border-radius: 12px;
    padding: 0.7rem 1rem !important; /* Adjust message padding */
    margin: 0.25rem 0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05); /* Subtle shadow on bot messages */
}
"""

def generate_response(message, history):
    """
    Function to call the OpenRouter API with the user's message and stream the response.
    Returns:
    - Updated history for the chatbot component
    - Updated history for the state variable
    - An empty string for the textbox component to clear it
    """
    if not OPENROUTER_API_KEY:
        error_message = "Error: OPENROUTER_API_KEY not set. Please set this environment variable."
        history.append((message, error_message))
        yield history, history, ""
        return

    # Add the user's message to the history first, for immediate display
    history.append((message, ""))
    yield history, history, ""

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if bot_msg:
            messages.append({"role": "assistant", "content": bot_msg})

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "stream": True
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        full_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    line_data = decoded_line[6:].strip()
                    if line_data == '[DONE]':
                        break
                    
                    json_data = json.loads(line_data)
                    chunk = json_data['choices'][0]['delta'].get('content', '')
                    full_response += chunk
                    history[-1] = (message, full_response)
                    yield history, history, ""
                    
    except requests.exceptions.RequestException as e:
        history[-1] = (message, f"An error occurred: {e}")
        yield history, history, ""
    except Exception as e:
        history[-1] = (message, f"An unexpected error occurred: {e}")
        yield history, history, ""

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    state = gr.State(value=[])
    
    with gr.Column(elem_classes="main-chat-area"):
        # The welcome text and subtitle, visible on the front page
        gr.Markdown("# Introducing GPT-5", elem_id="welcome-header")
        gr.Markdown("ChatGPT now has our smartest, fastest, most useful model yet, with thinking built in—so you get the best answer, every time.", elem_id="welcome-subtitle")

        chatbot = gr.Chatbot(elem_id="chatbot", label=None)
        
        with gr.Column(elem_classes="chat-input-area"):
            with gr.Row(elem_classes="input-box", variant="panel"):
                msg = gr.Textbox(
                    placeholder="+ Ask anything",
                    elem_id="user-input",
                    lines=1,
                    scale=9,
                    container=False
                )
                send_button = gr.Button(
                    value="",
                    elem_classes="send-button",
                    variant="primary",
                    scale=1
                )

    # Event handlers
    msg.submit(
        generate_response,
        [msg, state],
        [chatbot, state, msg]
    )
    send_button.click(
        generate_response,
        [msg, state],
        [chatbot, state, msg]
    )

demo.queue().launch()
