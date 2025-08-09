import gradio as gr
import requests
import os

# Your API key logic
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

def generate_response_streaming(message, history):
    """
    Streaming response generator that yields partial responses
    """
    if not OPENROUTER_API_KEY:
        yield "Error: OPENROUTER_API_KEY not set."
        return
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Build messages from history
    messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if bot_msg:  # Only add bot message if it exists
            messages.append({"role": "assistant", "content": bot_msg})
    
    messages.append({"role": "user", "content": message})
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "stream": True,  # Enable streaming
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]  # Remove 'data: ' prefix
                    if line.strip() == '[DONE]':
                        break
                    try:
                        import json
                        data = json.loads(line)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                full_response += delta['content']
                                yield full_response
                    except json.JSONDecodeError:
                        continue
                        
    except requests.exceptions.RequestException as e:
        yield f"An error occurred: {e}"

# Create the ChatInterface with streaming and additional features
demo = gr.ChatInterface(
    generate_response_streaming,
    type="messages",  # Use the modern messages format
    theme=gr.themes.Glass(),  # Keep your Glass theme
    title="My Glassy Streaming Chatbot",
    description="A streaming chatbot powered by OpenRouter API",
    flagging_mode="manual",  # Enable manual flagging like in the example
    flagging_options=["Like", "Spam", "Inappropriate", "Other"],  # Flagging options
    save_history=True,  # Save chat history
    retry_btn=True,  # Add retry button
    undo_btn=True,   # Add undo button
    clear_btn=True,  # Add clear button
)

if __name__ == "__main__":
    demo.launch()