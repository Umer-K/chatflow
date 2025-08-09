import gradio as gr
import requests
import os
import json

# Set your OpenRouter API key as a secret on Hugging Face Spaces
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Define the custom CSS for the full-screen layout
custom_css = """
/* The main container for the Gradio app, fills the entire viewport */
.gradio-container {
    height: 100vh;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
}

/* Main chat area styling, applies to the ChatInterface content */
.gradio-app {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}

/* Chat message bubbles */
.gradio-app .message-wrap.user {
    background-color: var(--button-primary-background-color) !important;
    color: var(--button-primary-text-color) !important;
}
.gradio-app .message-wrap.bot {
    background-color: var(--background-fill-primary) !important;
    color: var(--body-text-color) !important;
}

/* Input area styling */
.gradio-app .chat-input-area {
    background-color: var(--background-fill-secondary);
}

.gradio-app .input-box {
    max-width: 800px;
    margin: 0 auto;
    background-color: var(--background-fill-primary);
    border-radius: var(--radius-xl);
    border: 1px solid var(--border-color-primary);
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
}

/* Input text box */
.gradio-app .scroll-hide::-webkit-scrollbar {
    width: 0;
}
.gradio-app .scroll-hide {
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
}
.gradio-app textarea {
    border: none !important;
    background: transparent !important;
    color: var(--body-text-color) !important;
    padding: 0.5rem !important;
    font-size: 1rem !important;
    resize: none !important;
    outline: none !important;
}

/* Send button styling */
.gradio-app .send-button {
    background: none !important;
    border: none !important;
    cursor: pointer;
    padding: 0.5rem;
}
.gradio-app .send-button svg {
    width: 20px;
    height: 20px;
    fill: var(--body-text-color) !important;
}

/* Hide the default chat header */
.gradio-app .panel-header {
    display: none;
}
"""

def generate_response(message, history):
    """
    Function to call the OpenRouter API with the user's message and stream the response.
    gr.ChatInterface automatically manages the history list of tuples for you.
    """
    if not OPENROUTER_API_KEY:
        yield "Error: OPENROUTER_API_KEY not set. Please set this environment variable."
        return

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prepare the message history for the API call
    messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if bot_msg: # Only append if not an empty string for the last message
            messages.append({"role": "assistant", "content": bot_msg})
    
    # Append the new user message
    messages.append({"role": "user", "content": message})

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "stream": True # Enable streaming
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
                    yield full_response
                    
    except requests.exceptions.RequestException as e:
        yield f"An error occurred: {e}"
    except Exception as e:
        yield f"An unexpected error occurred: {e}"

# The simplified Gradio interface using the ChatInterface component
demo = gr.ChatInterface(
    fn=generate_response,
    theme="abidlabs/Halving",
    css=custom_css,
    title="Aesthetic Chatbot",
    description="How can I help you today?"
)

demo.launch()