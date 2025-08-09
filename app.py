import gradio as gr
import requests
import os

# Set your OpenRouter API key as a secret on Hugging Face Spaces
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# --- Chatbot API Logic ---
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
    messages = [{"role": "system", "content": "You are a helpful AI assistant with a creative and friendly personality."}]
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
        
        # Stream the response back to Gradio for a better user experience
        yield "" # Yield an empty string to clear the input
        for chunk in bot_reply.split():
            yield chunk + " "
    
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

# --- Gradio Interface ---
# Use the gr.ChatInterface to automatically get a chatbot layout
demo = gr.ChatInterface(
    fn=generate_response,
    theme="ysj103135/anime_dark",  # Use the specified community theme
    title="Aesthetic AI Chatbot",
    description="Ask me anything!"
)

# Launch the app
demo.launch()