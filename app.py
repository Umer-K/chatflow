import gradio as gr
import requests
import os

# Set your OpenRouter API key as a secret on Hugging Face Spaces
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Custom CSS for the full-screen, single-column layout
custom_css = """
/* The main container for the Gradio app, fills the entire viewport */
.gradio-container {
    height: 100vh;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
}

/* Main content area */
#main-chat-area {
    flex-grow: 1;
    background-color: var(--background-fill-secondary); /* Use theme variable */
    display: flex;
    flex-direction: column;
}

/* "How can I help you today?" header */
#welcome-header {
    text-align: center;
    color: var(--body-text-color);
    font-size: 2rem;
    font-weight: 500;
    padding-top: 10vh;
}

/* Chatbot component styling */
#chatbot {
    flex-grow: 1;
    overflow-y: auto;
    background-color: var(--background-fill-secondary);
    max-width: 800px;
    margin: 0 auto;
    padding: 1rem;
}

/* Chat message bubbles */
#chatbot .user-message {
    background-color: var(--button-primary-background-color) !important;
    color: var(--button-primary-text-color) !important;
}

#chatbot .bot-message {
    background-color: var(--background-fill-primary) !important;
    color: var(--body-text-color) !important;
}

/* Input area styling */
#chat-input-area {
    padding: 1rem 1.5rem;
    background-color: var(--background-fill-secondary);
}

#input-wrapper {
    max-width: 800px;
    margin: 0 auto;
    background-color: var(--background-fill-primary);
    border-radius: var(--radius-xl);
    border: 1px solid var(--border-color-primary);
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
}
#input-wrapper:focus-within {
    border-color: var(--button-primary-background-color);
}

#user-input {
    width: 100%;
    border: none;
    background: transparent;
    color: var(--body-text-color);
    padding: 0.5rem;
    font-size: 1rem;
    resize: none;
    outline: none;
}

#send-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
}
#send-button svg {
    width: 20px;
    height: 20px;
    fill: var(--body-text-color);
}
"""

def generate_response(message, chat_history):
    """
    Function to call the OpenRouter API with the user's message and stream the response.
    """
    if not OPENROUTER_API_KEY:
        yield "Error: OPENROUTER_API_KEY not set. Please set this environment variable."
        return
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    for user_msg, bot_msg in chat_history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})
    messages.append({"role": "user", "content": message})

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
    }

    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()

        # Create an empty string to hold the full response
        full_response = ""
        
        # Iterate over the response stream
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                # Append the new chunk and update the history
                full_response += chunk
                yield full_response
                
    except requests.exceptions.RequestException as e:
        yield f"An error occurred: {e}"

with gr.Blocks(theme="abidlabs/Halving", css=custom_css) as demo:
    # A single column to hold the welcome header, chatbot, and input area
    with gr.Column(elem_id="main-chat-area"):
        gr.Markdown("# How can I help you today?", elem_id="welcome-header")
        chatbot = gr.Chatbot(elem_id="chatbot", label="Chat History")
        
        with gr.Column(elem_id="chat-input-area"):
            with gr.Row(elem_id="input-wrapper"):
                msg = gr.Textbox(
                    label="Message the bot...",
                    elem_id="user-input",
                    lines=1,
                    scale=9,
                    container=False 
                )
                send_button = gr.Button(
                    value="Send",
                    elem_id="send-button",
                    variant="primary",
                    scale=1
                )

    # Function to handle user message submission
    def add_text_and_stream(history, text):
        history = history + [(text, None)]
        return history, gr.update(value="", interactive=False)

    # Event handlers
    # Update the history with the user's message and then stream the bot's response
    msg.submit(
        add_text_and_stream,
        [chatbot, msg],
        [chatbot, msg],
        queue=False
    ).then(
        generate_response,
        [msg, chatbot],
        chatbot
    )

    send_button.click(
        add_text_and_stream,
        [chatbot, msg],
        [chatbot, msg],
        queue=False
    ).then(
        generate_response,
        [msg, chatbot],
        chatbot
    )

demo.queue().launch()