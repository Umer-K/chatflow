import requests
import os
import json
import streamlit as st
from datetime import datetime
import pickle

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

# File to store chat history
HISTORY_FILE = "chat_history.json"

def load_chat_history():
    """Load chat history from file"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading chat history: {e}")
    return []

def save_chat_history(messages):
    """Save chat history to file"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error saving chat history: {e}")

def clear_chat_history():
    """Clear chat history file"""
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.session_state.messages = []
    except Exception as e:
        st.error(f"Error clearing chat history: {e}")

# Initialize session state with saved history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

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
        "google/gemini-pro",
        "meta-llama/llama-3.1-8b-instruct:free",
        "meta-llama/llama-3.1-70b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "meta-llama/llama-3.2-1b-instruct:free",
        "qwen/qwen-2-7b-instruct:free",
        "microsoft/phi-3-medium-4k-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "huggingface/zephyr-7b-beta:free",
        "openchat/openchat-7b:free",
        "gryphe/mythomist-7b:free",
        "undi95/toppy-m-7b:free",
        "openrouter/auto"
    ]
    
    selected_model = st.selectbox("Model", models, index=0)
    
    st.divider()
    
    # Chat History Controls
    st.header("Chat History")
    
    # Show number of messages
    if st.session_state.messages:
        st.info(f"Messages stored: {len(st.session_state.messages)}")
    
    # Auto-save toggle
    auto_save = st.checkbox("Auto-save messages", value=True)
    
    # Manual save/load buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save History", use_container_width=True):
            save_chat_history(st.session_state.messages)
            st.success("History saved!")
    
    with col2:
        if st.button("Load History", use_container_width=True):
            st.session_state.messages = load_chat_history()
            st.success("History loaded!")
            st.rerun()
    
    st.divider()
    
    # View History
    if st.button("View History File", use_container_width=True):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history_content = f.read()
            st.text_area("Chat History (JSON)", history_content, height=200)
        else:
            st.warning("No history file found")
    
    # Download History
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'rb') as f:
            st.download_button(
                label="Download History",
                data=f.read(),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    st.divider()
    
    # Clear controls
    if st.button("Clear Chat", use_container_width=True, type="secondary"):
        clear_chat_history()
        st.success("Chat cleared!")
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
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)
    
    # Auto-save if enabled
    if auto_save:
        save_chat_history(st.session_state.messages)
    
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
    assistant_message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(assistant_message)
    
    # Auto-save if enabled
    if auto_save:
        save_chat_history(st.session_state.messages)