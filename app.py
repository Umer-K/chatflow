import gradio as gr
import requests
import os

# Your API key logic
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

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
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

# Use the Soft theme
demo = gr.ChatInterface(
    generate_response,
    theme=gr.themes.Soft(),
    title="My Soft Chatbot"
)

demo.launch()