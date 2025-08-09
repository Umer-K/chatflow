import streamlit as st
import requests
import os
import json
import time

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="AI Assistant 2025",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern 2025 design
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 800px;
    }
    
    /* Title styling */
    .main-header {
        text-align: center;
        color: white;
        font-weight: 700;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .sub-header {
        text-align: center;
        color: rgba(255,255,255,0.8);
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Message styling */
    .stChatMessage {
        border-radius: 15px;
        margin-bottom: 1rem;
        padding: 1rem;
        backdrop-filter: blur(5px);
    }
    
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background: rgba(248, 250, 252, 0.8);
        border: 1px solid rgba(0,0,0,0.1);
    }
    
    /* Input styling */
    .stChatInput > div > div > div > div {
        background: rgba(255,255,255,0.9);
        border-radius: 25px;
        border: 2px solid transparent;
        backdrop-filter: blur(10px);
    }
    
    .stChatInput > div > div > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 1rem;
        background: rgba(248, 250, 252, 0.8);
        border-radius: 15px;
        margin-bottom: 1rem;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        margin: 0 2px;
        animation: typing 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False

# Check for API key
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

def get_ai_response(messages):
    """Get response from OpenRouter API"""
    if not OPENROUTER_API_KEY:
        return "❌ Error: OPENROUTER_API_KEY not set in environment variables."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prepare messages for API
    api_messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
    for msg in messages:
        api_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": api_messages,
        "stream": True,
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]
                    if line.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(line)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                full_response += delta['content']
                                yield full_response
                    except json.JSONDecodeError:
                        continue
                        
    except requests.exceptions.RequestException as e:
        yield f"❌ An error occurred: {e}"

# Header
st.markdown('<h1 class="main-header">🤖 AI Assistant 2025</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Powered by Advanced AI • Streamlit Interface</p>', unsafe_allow_html=True)

# Main chat container
with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here... ✨"):
        # Add user message to session state
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Show typing indicator briefly
            with message_placeholder.container():
                st.markdown("""
                <div class="typing-indicator">
                    <span style="margin-right: 10px;">AI is thinking</span>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
                """, unsafe_allow_html=True)
            
            time.sleep(0.5)  # Brief pause for effect
            
            # Stream the response
            full_response = ""
            for response_chunk in get_ai_response(st.session_state.messages):
                full_response = response_chunk
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
        # Add assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    st.markdown('</div>', unsafe_allow_html=True)

# Sidebar with controls
with st.sidebar:
    st.markdown("### 🛠️ Controls")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### 📊 Stats")
    st.metric("Messages", len(st.session_state.messages))
    
    if OPENROUTER_API_KEY:
        st.success("✅ API Key Connected")
    else:
        st.error("❌ API Key Missing")
        st.info("Set OPENROUTER_API_KEY environment variable")
    
    st.markdown("### ℹ️ About")
    st.info("Modern AI chat interface built with Streamlit. Features real-time streaming responses and a beautiful 2025 design.")