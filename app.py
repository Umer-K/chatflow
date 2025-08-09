import streamlit as st
import requests
import os
import json

# Page config
st.set_page_config(
    page_title="AI Assistant",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Enhanced styling with fixed transparent input
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* Clean header */
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
    }
    
    .main-subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #718096;
        margin-bottom: 3rem;
    }
    
    .welcome-message {
        text-align: center;
        font-size: 1.2rem;
        color: #4a5568;
        margin: 4rem 0;
    }
    
    /* User messages - Right aligned, blue */
    .stChatMessage[data-testid*="user"] {
        flex-direction: row-reverse !important;
        margin-left: 15% !important;
    }
    
    .stChatMessage[data-testid*="user"] .stMarkdown {
        background: #0066cc !important;
        color: white !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 12px 16px !important;
        margin-left: 12px !important;
    }
    
    /* AI messages - Left aligned, gray */
    .stChatMessage[data-testid*="assistant"] {
        margin-right: 15% !important;
    }
    
    .stChatMessage[data-testid*="assistant"] .stMarkdown {
        background: #f8f9fa !important;
        color: #2d3748 !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 12px 16px !important;
        margin-right: 12px !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* Hide avatars */
    .stChatMessage img { display: none !important; }

    /* Chat Input: Full Glass Fix */
    .stChatInputContainer,
    .stChatInputContainer div,
    .stChatInputContainer div:focus-within,
    .stChatInputContainer div:hover {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Outer input container styling */
    .stChatInputContainer > div {
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 24px !important;
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
    }

    /* The actual textarea */
    .stChatInputContainer textarea {
        background: transparent !important;
        color: white !important;
        border: none !important;
        padding: 12px 20px !important;
        font-size: 16px;
        resize: none;
    }

    /* Placeholder */
    .stChatInputContainer textarea::placeholder {
        color: rgba(255, 255, 255, 0.7) !important;
        opacity: 1;
    }

    /* Focus state */
    .stChatInputContainer textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# API key
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

def get_ai_response(messages, model="openai/gpt-3.5-turbo"):
    if not OPENROUTER_API_KEY:
        return "No API key found."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    api_messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    api_messages.extend(messages)
    
    data = {
        "model": model,
        "messages": api_messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        full_response = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:].strip()
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and data['choices']:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                full_response += delta['content']
                                yield full_response
                    except:
                        continue
    except Exception as e:
        yield "Sorry, something went wrong."

# Header
st.markdown('<h1 class="main-title">AI Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Ask me anything</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # API Status
    status = "Connected" if OPENROUTER_API_KEY else "No API Key"
    if status == "Connected":
        st.success("API Connected")
    else:
        st.error("No API Key")
    
    # Model
    models = ["openai/gpt-3.5-turbo", "openai/gpt-4", "anthropic/claude-3-haiku"]
    selected_model = st.selectbox("Model", models)
    
    # Clear
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Welcome message
if not st.session_state.messages:
    st.markdown('<div class="welcome-message">How can I help you today?</div>', unsafe_allow_html=True)

# Display chat messages
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
        for response in get_ai_response(st.session_state.messages, selected_model):
            full_response = response
            placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})