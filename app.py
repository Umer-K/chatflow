import gradio as gr
import requests
import os
import json

# Set your OpenRouter API key as a secret on Hugging Face Spaces
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Custom CSS for the full-screen, glowing Gen Z aesthetic
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

/* Base theme colors for our glow */
:root {
    --glowing-accent: #00ffff;  /* Neon cyan */
    --glowing-shadow: 0 0 10px var(--glowing-accent), inset 0 0 5px var(--glowing-accent);
}

/* Chat message bubbles */
.gradio-app .message-wrap.user {
    background-color: var(--glowing-accent) !important;
    color: #000000 !important; /* Use black text for contrast on cyan */
    border-radius: 12px;
}
.gradio-app .message-wrap.bot {
    background-color: var(--background-fill-primary) !important;
    color: var(--body-text-color) !important;
    border-radius: 12px;
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
    box-shadow: 0 0 5px rgba(0, 255, 255, 0.5); /* Subtle initial glow */
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    transition: box-shadow 0.3s ease;
}
.gradio-app .input-box:focus-within {
    border-color: var(--glowing-accent);
    box-shadow: var(--glowing-shadow); /* Stronger glow on focus */
}

/* Input text box */
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
    background: var(--background-fill-primary) !important;
    border: 1px solid var(--border-color-primary) !important;
    border-radius: var(--radius-xl) !important;
    cursor: pointer;
    padding: 0.5rem;
    box-shadow: 0 0 5px rgba(0, 255, 255, 0.5); /* Subtle initial glow */
    transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
.gradio-app .send-button:hover {
    border-color: var(--glowing-accent) !important;
    box-shadow: var(--glowing-shadow) !important; /* Stronger glow on hover */
}
.gradio-app .send-button svg {
    width: 20px;
    height: 20px;
    fill: var(--glowing-accent) !important;
}

/* Hide the default chat header */
.gradio-app .panel-header {
    display: none;
}
"""

def generate_response(message, history):
    if not OPENROUTER_API_KEY:
        yield "Error: OPENROUTER_API_KEY not set. Please set this environment variable."
        return

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
    
    messages.append({"role": "user", "content": message})

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
                    yield full_response
                    
    except requests.exceptions.RequestException as e:
        yield f"An error occurred: {e}"
    except Exception as e:
        yield f"An unexpected error occurred: {e}"

demo = gr.ChatInterface(
    fn=generate_response,
    theme="abidlabs/Halving",
    css=custom_css,
    title="Aesthetic Chatbot",
    description="How can I help you today?"
)

demo.launch()