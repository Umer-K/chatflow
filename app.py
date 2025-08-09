import gradio as gr
import requests
import os

# Set your OpenRouter API key as a secret on Hugging Face Spaces
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Revised Custom CSS to work with themes
custom_css = """
/* The main container for the entire Gradio app */
.gradio-container {
    display: flex !important;
    height: 100vh;
    padding: 0;
    margin: 0;
}

/* Sidebar styling */
#sidebar {
    width: 260px;
    background-color: var(--background-fill-primary); /* Use theme variable */
    padding: 1rem;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
}

#sidebar .new-chat-button, #sidebar .chat-history, #sidebar .user-profile {
    color: var(--body-text-color); /* Ensure text is visible */
}

/* Main chat area styling */
#main-chat-area {
    flex-grow: 1;
    background-color: var(--background-fill-secondary); /* Use theme variable */
    display: flex;
    flex-direction: column;
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
"""

def generate_response(message, history):
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY not set."
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    for user_msg, bot_msg in history:
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

        # Stream the response for better UX
        full_response = ""
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                # Assuming simple text streaming from the API
                full_response += chunk
                yield full_response
                
    except requests.exceptions.RequestException as e:
        yield f"An error occurred: {e}"

with gr.Blocks(theme="abidlabs/Halving", css=custom_css) as demo:
    with gr.Row(equal_height=True):
        with gr.Column(elem_id="sidebar", scale=1):
            gr.HTML(value="<div class='new-chat-button'>+ New Chat</div>", elem_classes="new-chat-button")
            gr.HTML(value="<div class='chat-history'><h3>Recent</h3><ul><li><a href='#'>Data Structures</a></li></ul></div>", elem_classes="chat-history")
            gr.HTML(value="<div class='user-profile'><div class='avatar'>U</div><span>Username</span></div>", elem_classes="user-profile")

        with gr.Column(elem_id="main-chat-area", scale=4):
            gr.Markdown("# How can I help you today?", elem_id="welcome-header")
            chatbot = gr.Chatbot(elem_id="chatbot")
            
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
    
    def respond(message, chat_history):
        chat_history.append((message, ""))
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot], queue=False).then(
        generate_response, [msg, chatbot], chatbot
    )
    send_button.click(respond, [msg, chatbot], [msg, chatbot], queue=False).then(
        generate_response, [msg, chatbot], chatbot
    )

demo.queue().launch()