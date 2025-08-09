import requests
import os
import json
import time
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI Assistant",
    page_icon="💬",
    initial_sidebar_state="collapsed"
)

# Professional styling - ChatGPT inspired
st.markdown("""
<style>
    /* Import clean fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global app styling */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 400;
    }
    
    /* Hide Streamlit branding and clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container - centered and spacious */
    .main .block-container {
        max-width: 800px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Professional header styling */
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    
    .main-subtitle {
        font-size: 1.1rem;
        color: #718096;
        margin-bottom: 3rem;
        font-weight: 400;
    }
    
    /* Welcome message - centered */
    .welcome-message {
        text-align: center;
        font-size: 1.2rem;
        color: #4a5568;
        margin: 4rem 0;
        font-weight: 400;
        line-height: 1.6;
    }
    
    /* Chat messages styling */
    .stChatMessage {
        border: none !important;
        margin-bottom: 1rem;
        border-radius: 16px !important;
    }
    
    /* User messages - Right side, blue */
    .stChatMessage[data-testid*="user"] {
        flex-direction: row-reverse !important;
        margin-left: 15% !important;
        margin-right: 0% !important;
    }
    
    .stChatMessage[data-testid*="user"] .stMarkdown {
        background-color: #007bff !important;
        color: white !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 12px 16px !important;
        margin-left: 12px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }
    
    /* AI messages - Left side, light gray */
    .stChatMessage[data-testid*="assistant"] {
        margin-right: 15% !important;
        margin-left: 0% !important;
    }
    
    .stChatMessage[data-testid*="assistant"] .stMarkdown {
        background-color: #f8f9fa !important;
        color: #2d3748 !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 12px 16px !important;
        margin-right: 12px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* Hide chat avatars */
    .stChatMessage img {
        display: none !important;
    }
    
    /* Fixed chat input styling - removed problematic background */
    .stChatInputContainer {
        border: none !important;
        background: transparent !important;
        padding: 1rem 0 !important;
    }
    
    .stChatInputContainer > div {
        border: 2px solid #e2e8f0 !important;
        border-radius: 24px !important;
        background: white !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        overflow: hidden !important;
    }
    
    .stChatInputContainer textarea {
        border: none !important;
        background: white !important;
        padding: 12px 20px !important;
        font-size: 1rem !important;
        color: #2d3748 !important;
        font-family: 'Inter', sans-serif !important;
        resize: none !important;
        outline: none !important;
    }
    
    .stChatInputContainer textarea::placeholder {
        color: #a0aec0 !important;
        font-weight: 400 !important;
    }
    
    .stChatInputContainer textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255,255,255,0.95) !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    /* Clean buttons */
    .stButton > button {
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        background: white !important;
        color: #374151 !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    .stButton > button:hover {
        background: #f9fafb !important;
        border-color: #9ca3af !important;
    }
    
    /* Status indicators */
    .stSuccess, .stError, .stWarning {
        border-radius: 8px !important;
        border: none !important;
        font-weight: 500 !important;
    }
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

# Clean, professional header
st.markdown('<h1 class="main-title">AI Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Ask me anything</p>', unsafe_allow_html=True)

# Sidebar (collapsed by default)
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
    st.markdown(
        '<div class="welcome-message">How can I help you today?</div>',
        unsafe_allow_html=True
    )

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input with inviting placeholder
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