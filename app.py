import gradio as gr
import requests
import os

# Define the model to use for the chatbot
CHATBOT_MODEL = "openai/gpt-3.5-turbo"

# --- OPENROUTER API LOGIC ---
# The OpenRouter API key will be read from an environment variable.
# On Hugging Face Spaces, you can set this in the "Secrets" section.
def get_openrouter_api_key():
    """Retrieves the OpenRouter API key from environment variables."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return api_key

def generate_response(message, history):
    """
    Sends a message and the chat history to the OpenRouter API to generate a response.
    
    Args:
        message (str): The user's new message.
        history (list): A list of tuples containing previous user/bot messages.
    
    Returns:
        str: The AI's generated response or an error message.
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        return "Error: OPENROUTER_API_KEY is not set. Please configure it in the environment secrets."
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Construct the messages list for the API call, including the system prompt
    # and all previous messages from the history.
    messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})
    messages.append({"role": "user", "content": message})

    data = {
        "model": CHATBOT_MODEL,
        "messages": messages,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        result = response.json()
        
        # Extract and return the chatbot's response
        return result['choices'][0]['message']['content']

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

# --- GRADIO UI & THEME ---
# Create a custom theme to replicate the '2025 green glowing' aesthetic.
custom_theme = gr.themes.Soft(
    # Set the primary and secondary hues to create the green glow effect
    primary_hue="emerald",  # Use a vibrant green hue
    secondary_hue="gray",
    font=[gr.themes.GoogleFont("DM Sans"), "sans-serif"],
).set(
    # Set the background to a deep black
    body_background_fill="#030712",
    # Style the text box and submit button to match the theme
    block_background_fill="#1F2937",
    block_border_color="#34D399", # Glowing green border
    block_border_width="2px",
    block_border_radius="25px",
    button_background_fill="#34D399",
    button_background_fill_hover="#10B981",
    button_text_color="#1F2937",
    button_border_radius="25px",
    
    # Set text colors
    text_color="#34D399",
    background_fill_primary="#030712", # Main background color
    background_fill_secondary="#1F2937",
)

# Custom CSS to style the chatbot messages and container, fixing the TypeError.
custom_css = """
.gradio-container {
    background-color: #030712;
    color: #34D399;
}
.gradio-chatbot {
    background-color: #1F2937;
    border: none;
    border-radius: 8px;
}
.gradio-chatbot .message.bot {
    background-color: #111827;
    border-radius: 10px;
}
.gradio-chatbot .message.user {
    background-color: #374151;
    border-radius: 10px;
}
"""

# Use the custom theme with the ChatInterface
demo = gr.ChatInterface(
    generate_response,
    theme=custom_theme,
    title="My Cyber Chatbot",
    textbox=gr.Textbox(
        placeholder="Ask anything",
        container=False,
        show_copy_button=True
    ),
    retry_btn=None,
    undo_btn=None,
    clear_btn="Clear Chat",
    css=custom_css,
)

# Launch the app
demo.launch()
