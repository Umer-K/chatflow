import gradio as gr
import requests
import os

# Set your OpenRouter API key.
# It's best practice to use environment variables for keys.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Custom CSS to replicate the dark theme and layout
custom_css = """
/* The main container for the entire Gradio app */
.gradio-container {
    display: flex !important;
    height: 100vh;
    padding: 0;
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
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

/* The new chat button */
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

/* Placeholder for chat history - a scrollable area */
#chat-history {
    margin-top: 1.5rem;
    flex-grow: 1;
    overflow-y: auto;
    list-style-type: none;
    color: #dbdee1;
}

/* User profile placeholder */
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

/* The main chat area - takes up the remaining space */
#main-chat-area {
    flex-grow: 1;
    background-color: #2b2d31;
    display: flex;
    flex-direction: column;
}

/* The chatbot component itself */
#chatbot {
    flex-grow: 1;
    overflow-y: auto;
    background-color: #2b2d31;
    max-width: 800px;
    margin: 0 auto;
}

/* The chat input area wrapper */
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

/* Customize chat bubble styles */
/* Gradio's chat component adds specific classes for user and bot messages. */
/* You might need to inspect the final HTML to get the exact class names. */
/* For example, for user messages, it might be something like .user-message */
/* and for bot messages, .bot-message. Let's use the default ones. */

/* User message bubble */
.user-message {
    background-color: #383a40 !important;
    color: #dbdee1 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

/* Bot message bubble */
.bot-message {
    background-color: #1e1f22 !important;
    color: #dbdee1 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
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

    # Format the messages for the API call. History is a list of tuples.
    messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})
    
    messages.append({"role": "user", "content": message})

    data = {
        "model": "openai/gpt-3.5-turbo", # Specify the model here
        "messages": messages,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Raise an exception for bad status codes
        
        result = response.json()
        bot_reply = result['choices'][0]['message']['content']
        
        return bot_reply

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

# Build the Gradio interface
with gr.Blocks(css=custom_css, theme=gr.themes.Monochrome()) as demo:
    with gr.Row():
        with gr.Column(elem_id="sidebar", scale=1):
            gr.HTML(value="<div id='new-chat-button'>+ New Chat</div>", elem_id="new-chat-button")
            gr.HTML(value="<div id='chat-history'><h3>Recent</h3><ul><li>Data Structures</li></ul></div>", elem_id="chat-history")
            gr.HTML(value="<div id='user-profile'><div class='avatar'>U</div><span>Username</span></div>", elem_id="user-profile")

        with gr.Column(elem_id="main-chat-area", scale=4):
            gr.Markdown("# How can I help you today?")
            gr.Chatbot(elem_id="chatbot")
            
            with gr.Column(elem_id="chat-input-area"):
                with gr.Row(elem_id="input-wrapper"):
                    msg = gr.Textbox(
                        label="Message the bot...",
                        elem_id="user-input",
                        lines=1,
                        scale=9
                    )
                    send_button = gr.Button(
                        value="Send",
                        elem_id="send-button",
                        variant="primary",
                        scale=1
                    )
    
    # Define the chat flow
    def respond(message, chat_history):
        bot_message = generate_response(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history

    msg.submit(respond, [msg, gr.State([])], [msg, gr.Chatbot(elem_id="chatbot")])
    send_button.click(respond, [msg, gr.State([])], [msg, gr.Chatbot(elem_id="chatbot")])

# Launch the app
demo.launch(share=True)