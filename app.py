import streamlit as st
import time
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match the React design
st.markdown("""
<style>
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #E5E7EB;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
    }
    
    /* Header styling */
    .header-container {
        background: white;
        border-bottom: 1px solid #E5E7EB;
        padding: 1rem;
        margin: -1rem -1rem 1rem -1rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .header-avatar {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #3B82F6 0%, #9333EA 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
    }
    
    .header-text h1 {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
        color: #1F2937;
    }
    
    .header-text p {
        margin: 0;
        font-size: 0.875rem;
        color: #6B7280;
    }
    
    /* Message styling */
    .user-message {
        background-color: #3B82F6;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        border-bottom-right-radius: 4px;
        margin: 0.5rem 0;
        max-width: 70%;
        float: right;
        clear: both;
    }
    
    .assistant-message {
        background-color: white;
        color: #1F2937;
        padding: 0.75rem 1rem;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        border-bottom-left-radius: 4px;
        margin: 0.5rem 0;
        max-width: 70%;
        float: left;
        clear: both;
    }
    
    /* Avatar styling */
    .message-container {
        display: flex;
        align-items: flex-start;
        margin: 1rem 0;
        gap: 12px;
    }
    
    .message-container.user {
        flex-direction: row-reverse;
    }
    
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 14px;
    }
    
    .avatar.user {
        background-color: #3B82F6;
        color: white;
    }
    
    .avatar.assistant {
        background-color: #E5E7EB;
        color: #6B7280;
    }
    
    /* Welcome screen styling */
    .welcome-container {
        text-align: center;
        padding: 3rem 0;
    }
    
    .welcome-icon {
        width: 64px;
        height: 64px;
        background: linear-gradient(135deg, #3B82F6 0%, #9333EA 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem;
        color: white;
        font-size: 32px;
    }
    
    .example-prompt {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
    }
    
    .example-prompt:hover {
        border-color: #93C5FD;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Input area styling */
    .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #D1D5DB !important;
        padding: 0.75rem !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #3B82F6 0%, #6366F1 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #2563EB 0%, #4F46E5 100%);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Status indicator */
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.875rem;
        margin-top: 1rem;
    }
    
    .status-indicator.ready {
        color: #10B981;
    }
    
    .status-indicator.error {
        color: #EF4444;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    .status-dot.ready {
        background-color: #10B981;
    }
    
    .status-dot.error {
        background-color: #EF4444;
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    /* Loading animation */
    .loading-dots {
        display: flex;
        gap: 4px;
        padding: 0.75rem 1rem;
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        border-bottom-left-radius: 4px;
        width: fit-content;
    }
    
    .loading-dot {
        width: 8px;
        height: 8px;
        background-color: #9CA3AF;
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    
    .loading-dot:nth-child(1) {
        animation-delay: -0.32s;
    }
    
    .loading-dot:nth-child(2) {
        animation-delay: -0.16s;
    }
    
    @keyframes bounce {
        0%, 80%, 100% {
            transform: scale(0);
        }
        40% {
            transform: scale(1);
        }
    }
    
    /* API Key input styling */
    .stTextInput input {
        border-radius: 8px !important;
        border: 1px solid #D1D5DB !important;
        padding: 0.5rem !important;
        font-family: monospace !important;
    }
    
    .api-key-section {
        background: #FEF3C7;
        border: 1px solid #FCD34D;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .api-key-section h4 {
        color: #92400E;
        margin-bottom: 0.5rem;
    }
    
    .api-key-section p {
        color: #78350F;
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = 'openai/gpt-3.5-turbo'
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# Model options
models = {
    'openai/gpt-3.5-turbo': 'GPT-3.5 Turbo',
    'openai/gpt-4': 'GPT-4',
    'openai/gpt-4-turbo': 'GPT-4 Turbo',
    'anthropic/claude-3-haiku': 'Claude 3 Haiku',
    'anthropic/claude-3-opus': 'Claude 3 Opus',
    'anthropic/claude-3-sonnet': 'Claude 3 Sonnet',
    'google/gemini-pro': 'Gemini Pro',
    'google/gemini-pro-1.5': 'Gemini Pro 1.5',
    'meta-llama/llama-3-70b-instruct': 'Llama 3 70B',
    'mistralai/mixtral-8x7b-instruct': 'Mixtral 8x7B'
}

def call_openrouter_api(messages, model, api_key):
    """Call OpenRouter API with the given messages and model."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:8501",  # Optional, can be your app URL
            "X-Title": "AI Assistant",  # Optional, shows in OpenRouter dashboard
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'], None
        else:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            return None, error_msg
            
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return None, f"Connection error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # API Key Section
    st.markdown("""
    <div class="api-key-section">
        <h4>🔑 OpenRouter API Key</h4>
        <p>Get your API key from <a href="https://openrouter.ai/keys" target="_blank">openrouter.ai/keys</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    api_key_input = st.text_input(
        "API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="sk-or-v1-...",
        help="Your OpenRouter API key for accessing AI models",
        label_visibility="collapsed"
    )
    
    if api_key_input:
        st.session_state.api_key = api_key_input
    
    st.markdown("---")
    
    # Model selection
    st.markdown("### 🤖 AI Model")
    st.session_state.selected_model = st.selectbox(
        "Select Model",
        options=list(models.keys()),
        format_func=lambda x: models[x],
        key="model_select",
        label_visibility="collapsed"
    )
    
    # Model info
    st.info(f"📊 Using: {models[st.session_state.selected_model]}")
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # API Status
    if st.session_state.api_key:
        st.markdown("""
        <div class="status-indicator ready">
            <div class="status-dot ready"></div>
            <span>API Ready</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-indicator error">
            <div class="status-dot error"></div>
            <span>API Key Required</span>
        </div>
        """, unsafe_allow_html=True)

# Main chat area
col1, col2, col3 = st.columns([1, 6, 1])

with col2:
    # Header
    st.markdown(f"""
    <div class="header-container">
        <div class="header-avatar">🤖</div>
        <div class="header-text">
            <h1>AI Assistant</h1>
            <p>Powered by {models[st.session_state.selected_model]}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if API key is set
    if not st.session_state.api_key:
        st.warning("⚠️ Please enter your OpenRouter API key in the sidebar to start chatting.")
        st.markdown("""
        ### How to get started:
        1. Go to [OpenRouter](https://openrouter.ai/keys) and sign up/login
        2. Create a new API key
        3. Paste it in the sidebar
        4. Start chatting with your preferred AI model!
        """)
    
    # Message container
    messages_container = st.container()
    
    # Welcome screen or messages
    if not st.session_state.messages:
        with messages_container:
            st.markdown("""
            <div class="welcome-container">
                <div class="welcome-icon">⚡</div>
                <h2 style="color: #1F2937; margin-bottom: 0.5rem;">Welcome to AI Assistant</h2>
                <p style="color: #6B7280; margin-bottom: 1.5rem;">Start a conversation or try one of these examples:</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Example prompts
            example_prompts = [
                "Help me write a professional email",
                "Explain quantum computing in simple terms",
                "Give me 5 creative writing prompts",
                "What are the latest web development trends?"
            ]
            
            cols = st.columns(2)
            for i, prompt in enumerate(example_prompts):
                with cols[i % 2]:
                    if st.button(prompt, key=f"example_{i}", use_container_width=True):
                        st.session_state.input_text = prompt
                        st.rerun()
    else:
        # Display messages
        with messages_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="message-container user">
                        <div class="avatar user">👤</div>
                        <div class="user-message">{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="message-container">
                        <div class="avatar assistant">🤖</div>
                        <div class="assistant-message">{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Input area
    st.markdown("<br>", unsafe_allow_html=True)
    
    input_col1, input_col2 = st.columns([6, 1])
    
    with input_col1:
        user_input = st.text_area(
            "Type your message here...",
            key="user_input",
            height=70,
            value=st.session_state.input_text,
            label_visibility="collapsed",
            disabled=not st.session_state.api_key
        )
    
    with input_col2:
        send_button = st.button(
            "📤 Send", 
            use_container_width=True,
            disabled=not st.session_state.api_key
        )
    
    # Handle send
    if send_button and user_input and st.session_state.api_key:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Prepare messages for API
        api_messages = []
        for msg in st.session_state.messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Show loading animation
        with messages_container:
            with st.spinner("Thinking..."):
                # Call OpenRouter API
                response_content, error = call_openrouter_api(
                    api_messages, 
                    st.session_state.selected_model,
                    st.session_state.api_key
                )
                
                if error:
                    st.error(f"❌ {error}")
                    # Add error message to chat
                    error_response = f"Sorry, I encountered an error: {error}\n\nPlease check your API key and try again."
                    st.session_state.messages.append({"role": "assistant", "content": error_response})
                else:
                    # Add assistant response
                    st.session_state.messages.append({"role": "assistant", "content": response_content})
        
        # Clear input
        st.session_state.input_text = ""
        st.rerun()

# Auto-scroll to bottom (Streamlit does this automatically)
if st.session_state.messages:
    st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)

# Footer info
with col2:
    if st.session_state.api_key:
        st.markdown("---")
        st.caption("Connected to OpenRouter API | Chat powered by " + models[st.session_state.selected_model])
    else:
        st.markdown("---")
        st.caption("Not connected - Please add your OpenRouter API key in the sidebar")