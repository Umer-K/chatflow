import streamlit as st
import requests
import os
import json
import time

# Page configuration
st.set_page_config(
    page_title="AI Assistant 2025",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple CSS for chat layout - User right, AI left
st.markdown("""
<style>
    /* User messages - Right side */
    .stChatMessage[data-testid*="user"] {
        flex-direction: row-reverse !important;
        margin-left: 20% !important;
        margin-right: 0% !important;
    }
    
    .stChatMessage[data-testid*="user"] .stMarkdown {
        background-color: #007bff !important;
        color: white !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 12px 16px !important;
        margin-left: 8px !important;
        margin-right: 0px !important;
    }
    
    /* AI messages - Left side (default) */
    .stChatMessage[data-testid*="assistant"] {
        margin-right: 20% !important;
        margin-left: 0% !important;
    }
    
    .stChatMessage[data-testid*="assistant"] .stMarkdown {
        background-color: #f1f3f4 !important;
        color: #333 !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 12px 16px !important;
        margin-right: 8px !important;
        margin-left: 0px !important;
    }
    
    /* Hide avatars for cleaner look */
    .stChatMessage img {
        display: none !important;
    }
    
    /* Clean chat input */
    .stChatInputContainer {
        border-top: 1px solid #e0e0e0;
        padding-top: 1rem;
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
    """Simple API check"""
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
    """Get AI response"""
    if not OPENROUTER_API_KEY:
        return "❌ No API key found. Please add OPENROUTER_API_KEY to environment variables."
    
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
        response.raise_for_status()
        
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
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"❌ Error: {str(e)[:100]}..."

# Header
st.title("🤖 AI Assistant")
st.caption("Simple chat interface")

# Simple sidebar
with st.sidebar:
    st.header("Settings")
    
    # API Status
    status = check_api_status()
    if status == "Connected":
        st.success("✅ API Connected")
    elif status == "No API Key":
        st.error("❌ No API Key")
    else:
        st.warning("⚠️ Connection Issue")
    
    st.divider()
    
    # Model selection
    models = [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4",
        "anthropic/claude-3-haiku",
        "google/gemini-pro"
    ]
    
    selected_model = st.selectbox("Model", models)
    
    st.divider()
    
    # Controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Stats
    st.metric("Messages", len(st.session_state.messages))

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
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

# Simple footer
st.markdown("---")
st.markdown("🤖 **AI Assistant 2025** | Built with Streamlit")