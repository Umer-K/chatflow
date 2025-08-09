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
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://huggingface.co/spaces',
        'Report a bug': "https://huggingface.co/spaces",
        'About': "AI Assistant 2025 - Built with Streamlit 1.48.0"
    }
)

# Custom CSS for modern 2025 design with latest Streamlit compatibility
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
        max-width: 900px;
    }
    
    /* Title styling */
    .main-header {
        text-align: center;
        color: white;
        font-weight: 700;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { text-shadow: 2px 2px 4px rgba(0,0,0,0.3), 0 0 20px rgba(255,255,255,0.2); }
        to { text-shadow: 2px 2px 4px rgba(0,0,0,0.3), 0 0 30px rgba(255,255,255,0.4); }
    }
    
    .sub-header {
        text-align: center;
        color: rgba(255,255,255,0.8);
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Chat container - Updated for Streamlit 1.48.0 */
    .stChatMessage {
        border-radius: 20px !important;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    /* User messages */
    .stChatMessage[data-testid*="user"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
    }
    
    .stChatMessage[data-testid*="user"] .stMarkdown {
        color: white !important;
    }
    
    /* Assistant messages */
    .stChatMessage[data-testid*="assistant"] {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(0,0,0,0.1);
    }
    
    /* Chat input styling - Updated for latest version */
    .stChatInputContainer > div {
        background: rgba(255,255,255,0.9) !important;
        border-radius: 30px !important;
        border: 2px solid transparent !important;
        backdrop-filter: blur(15px) !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
    }
    
    .stChatInputContainer > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 25px rgba(102, 126, 234, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255,255,255,0.1) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Metrics styling */
    .metric-container {
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 1rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Improved scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    /* Loading animation */
    .stSpinner {
        border-top: 3px solid #667eea !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
        border-radius: 15px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 15px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 15px !important;
        backdrop-filter: blur(10px) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "message_count" not in st.session_state:
    st.session_state.message_count = 0

# Check for API key
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

@st.cache_data(ttl=3600)
def check_api_connection():
    """Check if API is working"""
    if not OPENROUTER_API_KEY:
        return False
    try:
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        response = requests.get(url, headers=headers, timeout=5)
        return response.status_code == 200
    except:
        return False

def stream_ai_response(messages):
    """Stream response from OpenRouter API with better error handling"""
    if not OPENROUTER_API_KEY:
        yield "❌ **Error:** OPENROUTER_API_KEY not set in environment variables."
        return
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://huggingface.co/spaces",
        "X-Title": "AI Assistant 2025"
    }
    
    # Prepare messages for API
    api_messages = [{"role": "system", "content": "You are a helpful, friendly, and knowledgeable AI assistant. Provide clear, accurate, and engaging responses."}]
    for msg in messages:
        api_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": api_messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 1000,
    }
    
    try:
        with requests.post(url, headers=headers, json=data, stream=True, timeout=30) as response:
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
                            
    except requests.exceptions.Timeout:
        yield "⏰ **Request timed out.** Please try again."
    except requests.exceptions.RequestException as e:
        yield f"❌ **Connection error:** {str(e)[:100]}..."
    except Exception as e:
        yield f"❌ **Unexpected error:** {str(e)[:100]}..."

# Header with animation
st.markdown('<h1 class="main-header">🤖 AI Assistant 2025</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">✨ Powered by Advanced AI • Modern Streamlit Interface ✨</p>', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👨‍💻"):
        st.markdown(message["content"])

# Chat input - MUST be at root level, not inside columns
if prompt := st.chat_input("💭 Type your message here... ✨"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.message_count += 1
    
    with st.chat_message("user", avatar="👨‍💻"):
        st.markdown(prompt)
    
    # Generate AI response
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        
        # Stream the response
        full_response = ""
        for response_chunk in stream_ai_response(st.session_state.messages):
            full_response = response_chunk
            message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        
    # Add assistant response to session state
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Enhanced sidebar
with st.sidebar:
    st.markdown("### 🛠️ **Chat Controls**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.session_state.message_count = 0
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("### 📊 **Statistics**")
    st.markdown(f'<div class="metric-container"><strong>Messages:</strong> {st.session_state.message_count}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-container"><strong>Conversations:</strong> {len(st.session_state.messages)}</div>', unsafe_allow_html=True)
    
    st.markdown("### 🔐 **API Status**")
    if OPENROUTER_API_KEY:
        if check_api_connection():
            st.success("✅ **Connected & Ready**")
        else:
            st.warning("⚠️ **API Key Set** (Connection not verified)")
    else:
        st.error("❌ **API Key Missing**")
        st.info("💡 Add OPENROUTER_API_KEY in Space secrets")
    
    st.markdown("### ℹ️ **About**")
    st.info("""
    **AI Assistant 2025**
    
    🚀 **Features:**
    - Real-time streaming responses
    - Modern gradient UI design  
    - Optimized for latest Streamlit
    - Smart conversation handling
    
    Built with ❤️ using Streamlit 1.48.0
    """)
    
    # Add some fun stats
    if st.session_state.messages:
        total_chars = sum(len(msg["content"]) for msg in st.session_state.messages)
        st.markdown(f'<div class="metric-container"><strong>Total Characters:</strong> {total_chars:,}</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: rgba(255,255,255,0.7); padding: 1rem;'>"
    "🤖 <strong>AI Assistant 2025</strong> • Built with Streamlit • Powered by OpenRouter"
    "</div>", 
    unsafe_allow_html=True
)