import streamlit as st
import requests
import os
import json
import time
from datetime import datetime

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="AI Assistant 2025",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io/develop/api-reference/chat',
        'Report a bug': "https://github.com/streamlit/streamlit/issues",
        'About': "AI Assistant 2025 - Built with Streamlit's native chat components"
    }
)

# Streamlit's built-in theme with minimal custom CSS
st.markdown("""
<style>
    /* Minimal custom styling to enhance built-in components */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Enhanced chat input */
    .stChatInputContainer {
        border-top: 1px solid #e6e6e6;
        padding-top: 1rem;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-connected {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state using Streamlit patterns
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add welcome message
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! I'm your AI Assistant. How can I help you today? 🤖",
        "timestamp": datetime.now()
    })

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(int(time.time()))

# API Configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
DEFAULT_MODEL = "openai/gpt-3.5-turbo"

@st.cache_data(ttl=300, show_spinner=False)
def get_available_models():
    """Fetch available models from OpenRouter"""
    if not OPENROUTER_API_KEY:
        return [DEFAULT_MODEL]
    
    try:
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            models = response.json()
            return [model["id"] for model in models.get("data", [])][:20]  # Limit to 20 models
    except:
        pass
    
    return [DEFAULT_MODEL]

@st.cache_data(ttl=600, show_spinner=False)
def check_api_status():
    """Check API connection status"""
    if not OPENROUTER_API_KEY:
        return "no_key"
    
    try:
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        response = requests.get(url, headers=headers, timeout=5)
        return "connected" if response.status_code == 200 else "error"
    except:
        return "error"

def stream_ai_response(messages, model=DEFAULT_MODEL, temperature=0.7):
    """Stream response from OpenRouter API"""
    if not OPENROUTER_API_KEY:
        yield "❌ **Error:** OPENROUTER_API_KEY not found in environment variables."
        return
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Streamlit AI Assistant"
    }
    
    # Prepare API messages (exclude timestamp)
    api_messages = [
        {
            "role": "system", 
            "content": "You are a helpful, knowledgeable AI assistant. Provide clear, accurate responses. Use markdown formatting when appropriate."
        }
    ]
    
    for msg in messages:
        if msg["role"] in ["user", "assistant"]:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    payload = {
        "model": model,
        "messages": api_messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": 2000,
    }
    
    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=60) as response:
            if response.status_code != 200:
                yield f"❌ **API Error {response.status_code}:** {response.text[:200]}"
                return
            
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
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    full_response += delta['content']
                                    yield full_response
                        except json.JSONDecodeError:
                            continue
                            
    except requests.exceptions.Timeout:
        yield "⏰ **Request timed out.** Please try a shorter message or try again."
    except requests.exceptions.RequestException as e:
        yield f"🔌 **Connection error:** Unable to reach AI service. Please try again."
    except Exception as e:
        yield f"⚠️ **Unexpected error occurred.** Please refresh and try again."

# Header
st.title("🤖 AI Assistant 2025")
st.caption("Built with Streamlit's native chat components")

# Sidebar with enhanced controls
with st.sidebar:
    st.header("🛠️ Chat Settings")
    
    # API Status
    status = check_api_status()
    if status == "connected":
        st.markdown('<div class="status-indicator status-connected">🟢 API Connected</div>', unsafe_allow_html=True)
    elif status == "no_key":
        st.markdown('<div class="status-indicator status-error">🔴 No API Key</div>', unsafe_allow_html=True)
        st.error("Set OPENROUTER_API_KEY in environment variables")
    else:
        st.markdown('<div class="status-indicator status-warning">🟡 Connection Issues</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Model Selection
    available_models = get_available_models()
    selected_model = st.selectbox(
        "🤖 Select Model",
        available_models,
        index=0,
        help="Choose the AI model for responses"
    )
    
    # Temperature control
    temperature = st.slider(
        "🌡️ Creativity",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Higher values make responses more creative but less predictable"
    )
    
    st.divider()
    
    # Chat Controls
    st.subheader("💬 Chat Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            # Add welcome message back
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Chat cleared! How can I help you? 🤖",
                "timestamp": datetime.now()
            })
            st.rerun()
    
    with col2:
        if st.button("📁 New Session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_id = str(int(time.time()))
            st.session_state.messages.append({
                "role": "assistant",
                "content": "New session started! What would you like to discuss? 🌟",
                "timestamp": datetime.now()
            })
            st.rerun()
    
    # Export chat
    if len(st.session_state.messages) > 1:
        chat_export = "\n\n".join([
            f"**{msg['role'].title()}:** {msg['content']}" 
            for msg in st.session_state.messages
        ])
        st.download_button(
            "📥 Export Chat",
            chat_export,
            file_name=f"chat_export_{st.session_state.conversation_id}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.divider()
    
    # Statistics
    st.subheader("📊 Statistics")
    message_count = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
    total_chars = sum(len(msg["content"]) for msg in st.session_state.messages)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", message_count)
    with col2:
        st.metric("Characters", f"{total_chars:,}")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    quick_prompts = [
        "Explain a complex topic simply",
        "Help me write an email",
        "Generate creative ideas",
        "Analyze some data",
        "Write Python code"
    ]
    
    for prompt in quick_prompts:
        if st.button(f"💡 {prompt}", key=f"quick_{prompt}", use_container_width=True):
            # Add the quick prompt as a user message
            st.session_state.messages.append({
                "role": "user", 
                "content": prompt,
                "timestamp": datetime.now()
            })
            st.rerun()

# Main chat interface using Streamlit's built-in chat components
chat_container = st.container()

with chat_container:
    # Display chat messages using st.chat_message
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show timestamp for recent messages
            if hasattr(message, 'timestamp') or 'timestamp' in message:
                timestamp = message.get('timestamp', datetime.now())
                if isinstance(timestamp, datetime):
                    st.caption(f"*{timestamp.strftime('%H:%M:%S')}*")

# Chat input using Streamlit's built-in st.chat_input
if prompt := st.chat_input("💭 What can I help you with?"):
    # Add user message with timestamp
    user_message = {
        "role": "user", 
        "content": prompt,
        "timestamp": datetime.now()
    }
    st.session_state.messages.append(user_message)
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"*{user_message['timestamp'].strftime('%H:%M:%S')}*")
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Show typing indicator
        with st.spinner("🤔 Thinking..."):
            time.sleep(0.1)  # Brief pause for UX
        
        # Stream the response
        full_response = ""
        try:
            for response_chunk in stream_ai_response(
                st.session_state.messages, 
                model=selected_model,
                temperature=temperature
            ):
                full_response = response_chunk
                message_placeholder.markdown(full_response + "▌")
            
            # Remove cursor and show final response
            message_placeholder.markdown(full_response)
            
            # Add timestamp
            response_time = datetime.now()
            st.caption(f"*{response_time.strftime('%H:%M:%S')}*")
            
            # Add assistant response to session state
            assistant_message = {
                "role": "assistant", 
                "content": full_response,
                "timestamp": response_time
            }
            st.session_state.messages.append(assistant_message)
            
        except Exception as e:
            error_message = "❌ **Error:** Unable to generate response. Please try again."
            message_placeholder.markdown(error_message)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": error_message,
                "timestamp": datetime.now()
            })

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.875rem;'>
        🤖 <strong>AI Assistant 2025</strong> | 
        Built with <a href='https://streamlit.io' target='_blank'>Streamlit</a> | 
        Powered by <a href='https://openrouter.ai' target='_blank'>OpenRouter</a>
    </div>
    """, 
    unsafe_allow_html=True
)