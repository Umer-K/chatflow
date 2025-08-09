import requests
import os
import json
import streamlit as st

# Page configuration
st.set_page_config(page_title="AI Assistant", page_icon="💬")

# Background + hide the white container
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Hide the main container background */
    .main .block-container {
        background: transparent !important;
        padding: 1rem !important;
    }
    
    /* Make chat input area transparent */
    .stChatInputContainer {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# API function
def get_ai_response(messages):
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        yield "No API key found."
        return
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "system", "content": "You are a helpful AI assistant."}] + messages,
        "stream": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    line_str = line_str[6:]
                    if line_str.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(line_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                full_response += delta['content']
                                yield full_response
                    except:
                        continue
    except:
        yield "Error occurred. Please try again."

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        for response in get_ai_response(st.session_state.messages):
            full_response = response
            placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})