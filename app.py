import requests
import os
import json
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI Assistant",
    page_icon="💬",
    initial_sidebar_state="collapsed"
)

# White background
st.markdown("""
<style>
    .stApp {
        background: white;
    }
    
    .main .block-container {
        max-width: 800px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Get API key
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

@st.cache_data(ttl=300)
def check_api_status():
    if not OPENROUTER_API_KEY:
        return "No API Key"
    try:
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        response = requests.get(url, headers=headers, timeout=5)
        return "Connected" if response.status_code == 200 else "Error"
    except:
        return "Error"

def get_ai_response(messages, model="openai/gpt-3.5-turbo"):
    if not OPENROUTER_API_KEY:
        return "No API key found. Please add OPENROUTER_API_KEY to environment variables."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    
    api_messages = [{"role": "system", "content": "You are a helpful AI assistant. Provide clear and helpful responses."}]
    api_messages.extend(messages)
    
    data = {
        "model": model,
        "messages": api_messages,
        "stream": True,
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        response.raise_for_status()
        
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
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"Sorry, I encountered an error. Please try again."

# Header
st.title("AI Assistant")
st.caption("Ask me anything")

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # API Status
    status = check_api_status()
    if status == "Connected":
        st.success("API Connected")
    elif status == "No API Key":
        st.error("No API Key")
    else:
        st.warning("Connection Issue")
    
    st.divider()
    
    # Model selection
    models = [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4",
        "anthropic/claude-3-haiku",
        "google/gemini-pro"
    ]
    
    selected_model = st.selectbox("Model", models, index=0)
    
    st.divider()
    
    # Controls
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Show welcome message when no messages
if not st.session_state.messages:
    st.info("How can I help you today?")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        full_response = ""
        for response in get_ai_response(st.session_state.messages, selected_model):
            full_response = response
            placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
    
    # Add AI response to messages
    st.session_state.messages.append({"role": "assistant", "content": full_response})