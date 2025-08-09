import gradio as gr
import requests
import os

# Set your OpenRouter API key as a secret on Hugging Face Spaces
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Revised Custom CSS to fix color issues
custom_css = """
/* Global styles for text and background */
body {
    color: #dbdee1; /* Set a default light text color for better readability */
}

/* The main container for the entire Gradio app */
.gradio-container {
    display: flex !important;
    height: 100vh;
    padding: 0;
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: #2b2d31; /* Ensures the main background is dark */
}

/* Styles for the sidebar - a column on the left */
#sidebar {
    width: 260px;
    background-color: #1e1f22;
    padding: 1rem;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
}

/* New chat button styling */
#new-chat-button {
    border: 1px solid #4e4f52;
    padding: 0.75rem;
    border-radius: 8px;
    text-align: center;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
    color: #dbdee1;
}
#new-chat-button:hover {
    background-color: #35373c;
}

/* Chat history heading and links */
#chat-history h3 {
    font-size: 0.8rem;
    color: #b5bac1; /* Use a lighter gray for the heading */
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
#chat-history a {
    display: block;
    padding: 0.75rem;
    border-radius: 8px;
    text-decoration: none;
    color: #dbdee1; /* Ensure links are visible */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: background-color 0.2s;
}
#chat-history a:hover {
    background-color: #35373c;
}

/* User profile styling */
#user-profile {
    border-top: 1px solid #4e4f52;
    padding-top: 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-weight: 500;
    color: #dbdee1;
}
#user-profile .avatar {
    width: 32px;
    height: 32px;
    background-color: #5865f2;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

/* Main chat area styling */
#main-chat-area {
    flex-grow: 1;
    background-color: #2b2d31;
    display: flex;
    flex-direction: column;
}

/* "How can I help you today?" header */
#welcome-header {
    text-align: center;
    color: #dbdee1;
    font-size: 2rem;
    font-weight: 500;
    margin-top: 10vh; /* Position it like a welcome screen */
}

/* The chatbot component itself */
#chatbot {
    flex-grow: 1;
    overflow-y: auto;
    background-color: #2b2d31;
    max-width: 800px;
    margin: 0 auto;
}

/* Customize chat bubble styles */
/* Gradio's chat component adds specific classes for user and bot messages. */
/* We'll target these with the correct colors. */

/* User message bubble */
.user-message {
    background-color: #5865f2 !important; /* Use a distinct blue for user messages */
    color: #ffffff !important; /* White text for contrast */
    border-radius: 12px !important;
    padding: 1rem !important;
    margin-left: auto; /* Align user messages to the right */
    max-width: 70%;
}
.user-message .message-content {
    color: #ffffff !important;
}

/* Bot message bubble */
.bot-message {
    background-color: #383a40 !important; /* Darker background for bot messages */
    color: #dbdee1 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    margin-right: auto; /* Align bot messages to the left */
    max-width: 70%;
}
.bot-message .message-content {
    color: #dbdee1 !important;
}

/* The input area wrapper */
#chat-input-area {
    padding: 1rem 1.5rem;
    background-color: #2b2d31;
}

/* The input wrapper */
#input-wrapper {
    max-width: 800px;
    margin: 0 auto;
    background-color: #383a40;
    border-radius: 12px;
    border: 1px solid #4e4f52;
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
}
#input-wrapper:focus-within {
    border-color: #5865f2;
}

/* The textbox inside the input wrapper */
#user-input {
    flex-grow: 1;
    border: none;
    background: transparent;
    color: #dbdee1;
    padding: 0.5rem;
    font-size: 1rem;
    resize: none;
    outline: none;
}

/* The send button */
#send-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
}
#send-button svg {
    width: 20px;
    height: 20px;
    fill: #b5bac1;
    transition: fill 0.2s;
}
#send-button:hover svg {
    fill: #dbdee1;
}
"""

def generate_response(message, history):
    """
    Function to call the OpenRouter API with the user's message.
    """
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY not set. Please set this environment variable."
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Gradio's Chatbot history is a list of [user_message, bot_message] pairs.
    # Convert this to the OpenRouter format.
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
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        bot_reply = result['choices'][0]['message']['content']
        return bot_reply

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

# Build the Gradio interface
with gr.Blocks(css=custom_css, theme=gr.themes.Monochrome()) as demo:
    with gr.Row(equal_height=True):
        with gr.Column(elem_id="sidebar", scale=1):
            gr.HTML(value="<div id='new-chat-button'>+ New Chat</div>")
            gr.HTML(value="<div id='chat-history'><h3>Recent</h3><ul><li><a href='#'>Data Structures</a></li></ul></div>")
            gr.HTML(value="<div id='user-profile'><div class='avatar'>U</div><span>Username</span></div>")

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
                        container=False # This helps with styling by removing the outer container
                    )
                    send_button = gr.Button(
                        value="Send",
                        elem_id="send-button",
                        variant="primary",
                        scale=1
                    )
    
    # Define the chat flow
    def respond(message, chat_history):
        # Gradio's Chatbot expects a list of [user_message, bot_message] pairs.
        # Let's ensure our `generate_response` function can handle it.
        bot_message = generate_response(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    send_button.click(respond, [msg, chatbot], [msg, chatbot])

# Launch the app
demo.launch()