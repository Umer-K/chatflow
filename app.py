import requests
import os
import json
import streamlit as st
from datetime import datetime
import time

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
    
    /* Model category styling */
    .model-category {
        font-weight: bold;
        color: #1f77b4;
        padding: 4px 0;
    }
    
    .model-item {
        padding-left: 12px;
        font-size: 0.9em;
    }
    
    .free-badge {
        background-color: #28a745;
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 0.7em;
        margin-left: 8px;
    }
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
    """Check API connection status with timeout and error handling"""
    if not OPENROUTER_API_KEY:
        return "No API Key"
    try:
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        response = requests.get(url, headers=headers, timeout=10)
        return "Connected" if response.status_code == 200 else "Error"
    except requests.exceptions.Timeout:
        return "Timeout"
    except requests.exceptions.ConnectionError:
        return "Connection Error"
    except Exception:
        return "Error"

def get_model_categories():
    """
    Organize models by categories for better UX.
    Returns a dictionary with category names and their models.
    """
    return {
        "OpenAI Models": [
            ("GPT-3.5 Turbo", "openai/gpt-3.5-turbo", False)
        ],
        "Meta LLaMA Models": [
            ("LLaMA 3.1 8B Instruct", "meta-llama/llama-3.1-8b-instruct", False),
            ("LLaMA 3.1 70B Instruct", "meta-llama/llama-3.1-70b-instruct", False)
        ],
        "DeepSeek Models (Free)": [
            ("DeepSeek Chat v3", "deepseek/deepseek-chat-v3-0324:free", True),
            ("DeepSeek R1", "deepseek/deepseek-r1-0528:free", True)
        ],
        "Qwen Models (Free)": [
            ("Qwen3 Coder", "qwen/qwen3-coder:free", True)
        ],
        "Microsoft Models (Free)": [
            ("MAI DS R1", "microsoft/mai-ds-r1:free", True)
        ],
        "Google Models (Free)": [
            ("Gemma 3 27B Instruct", "google/gemma-3-27b-it:free", True),
            ("Gemma 3 4B Instruct", "google/gemma-3-4b-it:free", True)
        ],
        "Auto Selection": [
            ("Auto (Best Available)", "openrouter/auto", False)
        ]
    }

def format_model_display_name(name, is_free=False):
    """Format model name with free badge if applicable"""
    if is_free:
        return f"{name} 🆓"
    return name

def get_all_models():
    """Get flattened list of all models for selectbox"""
    categories = get_model_categories()
    models = []
    
    for category, model_list in categories.items():
        for name, model_id, is_free in model_list:
            display_name = format_model_display_name(name, is_free)
            models.append((display_name, model_id, category, is_free))
    
    return models

def validate_model_id(model_id):
    """Validate model ID format for safety"""
    # Basic validation to prevent injection attacks
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./:|')
    if not all(c in allowed_chars for c in model_id):
        return False
    
    # Check for reasonable length
    if len(model_id) > 100:
        return False
        
    return True

def get_ai_response(messages, model="openai/gpt-3.5-turbo"):
    """
    Get AI response with comprehensive error handling and streaming support
    """
    if not OPENROUTER_API_KEY:
        yield "⚠️ No API key found. Please add OPENROUTER_API_KEY to environment variables."
        return
    
    # Validate model ID
    if not validate_model_id(model):
        yield "⚠️ Invalid model ID detected. Please select a valid model."
        return
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Streamlit AI Assistant"
    }
    
    # Create system message and user messages
    system_prompt = "You are a helpful AI assistant. Provide clear, accurate, and helpful responses."
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(messages)
    
    # Adaptive parameters based on model type
    max_tokens = 4000 if "coder" in model.lower() else 2000
    temperature = 0.3 if "coder" in model.lower() else 0.7
    
    data = {
        "model": model,
        "messages": api_messages,
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=120)
        
        # Enhanced error handling
        if response.status_code != 200:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
            except:
                error_detail = f"HTTP {response.status_code}: {response.reason}"
            
            # Specific error messages for common issues
            if response.status_code == 401:
                yield "🔒 Authentication failed. Please check your API key."
            elif response.status_code == 429:
                yield "⏱️ Rate limit exceeded. Please wait a moment and try again."
            elif response.status_code == 400:
                yield f"⚠️ Request error: {error_detail}. Try a different model or shorter message."
            else:
                yield f"❌ API Error: {error_detail}. Please try a different model."
            return
        
        full_response = ""
        
        # Streaming response handling with better error recovery
        for line in response.iter_lines():
            if line:
                if line.startswith(b"data: "):
                    data_str = line[len(b"data: "):].decode("utf-8")
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                full_response += delta
                                yield full_response
                    except json.JSONDecodeError:
                        # Skip malformed JSON chunks
                        continue
                    except (KeyError, IndexError):
                        # Skip chunks with unexpected structure
                        continue
                            
    except requests.exceptions.Timeout:
        yield "⏱️ Request timed out. The model might be busy. Please try again or select a different model."
    except requests.exceptions.ConnectionError:
        yield "🌐 Connection error. Please check your internet connection and try again."
    except requests.exceptions.RequestException as e:
        yield f"🔧 Network error: {str(e)}. Please try again."
    except Exception as e:
        yield f"💥 Unexpected error: {str(e)}. Please try a different model or restart the application."

# Header
st.title("🤖 AI Assistant")
st.caption("Powered by multiple AI models - Ask me anything!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Status with enhanced display
    status = check_api_status()
    status_colors = {
        "Connected": ("🟢", "success"),
        "No API Key": ("🔴", "error"),
        "Timeout": ("🟡", "warning"),
        "Connection Error": ("🟡", "warning"),
        "Error": ("🔴", "error")
    }
    
    icon, alert_type = status_colors.get(status, ("🔴", "error"))
    if alert_type == "success":
        st.success(f"{icon} API Connected")
    elif alert_type == "error":
        st.error(f"{icon} {status}")
    else:
        st.warning(f"{icon} {status}")
    
    st.divider()
    
    # Enhanced model selection
    st.subheader("🎯 Model Selection")
    
    all_models = get_all_models()
    model_names = [model[0] for model in all_models]
    model_ids = [model[1] for model in all_models]
    model_categories = [model[2] for model in all_models]
    model_free_status = [model[3] for model in all_models]
    
    # Group models by category for better UX
    selected_index = st.selectbox(
        "Choose AI Model", 
        range(len(model_names)), 
        format_func=lambda x: model_names[x],
        index=0,
        help="🆓 indicates free models with no API costs"
    )
    
    selected_model = model_ids[selected_index]
    selected_category = model_categories[selected_index]
    is_free_model = model_free_status[selected_index]
    
    # Display model information
    st.caption(f"**Category:** {selected_category}")
    st.caption(f"**Model ID:** `{selected_model}`")
    
    if is_free_model:
        st.success("🆓 This model is free to use!")
    else:
        st.info("💳 This model may incur API costs")
    
    # Model-specific tips
    if "coder" in selected_model.lower():
        st.info("💻 **Coding Model:** Optimized for programming tasks")
    elif "deepseek" in selected_model.lower():
        st.info("🧠 **DeepSeek:** Advanced reasoning capabilities")
    elif "gemma" in selected_model.lower():
        st.info("🔍 **Gemma:** Efficient and fast responses")
    
    st.divider()
    
    # Chat History Controls
    st.subheader("💾 Chat History")
    
    # Show number of messages with better formatting
    if st.session_state.messages:
        user_msgs = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
        ai_msgs = sum(1 for msg in st.session_state.messages if msg["role"] == "assistant")
        st.metric("Total Messages", len(st.session_state.messages), f"{user_msgs} user, {ai_msgs} AI")
    else:
        st.info("No messages yet")
    
    # Auto-save toggle with description
    auto_save = st.checkbox(
        "Auto-save messages", 
        value=True,
        help="Automatically save conversation after each message"
    )
    
    # Manual save/load buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True):
            save_chat_history(st.session_state.messages)
            st.success("Saved!")
            time.sleep(1)
    
    with col2:
        if st.button("📁 Load", use_container_width=True):
            st.session_state.messages = load_chat_history()
            st.success("Loaded!")
            st.rerun()
    
    st.divider()
    
    # Export options
    st.subheader("📤 Export Options")
    
    # View History
    if st.button("👀 View History", use_container_width=True):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history_content = f.read()
            st.text_area("Chat History (JSON)", history_content, height=150)
        else:
            st.warning("No history file found")
    
    # Download History
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'rb') as f:
            st.download_button(
                label="⬇️ Download History",
                data=f.read(),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                help="Download chat history as JSON file"
            )
    
    st.divider()
    
    # Clear controls with confirmation
    st.subheader("🗑️ Reset Chat")
    if st.button("🚨 Clear All Messages", use_container_width=True, type="secondary"):
        if st.session_state.messages:  # Only show success if there were messages to clear
            clear_chat_history()
            st.success("Chat cleared!")
            st.rerun()
        else:
            st.info("Chat is already empty")

# Main chat interface
if not st.session_state.messages:
    # Enhanced welcome message
    st.info("""
    👋 **Welcome to AI Assistant!**
    
    🆓 **Free models available:** DeepSeek, Qwen3 Coder, Microsoft MAI, Google Gemma  
    💬 **How can I help you today?**
    
    Try asking about:
    - 💻 Programming and coding
    - 📊 Data analysis  
    - 🎓 Learning and explanations
    - 🎨 Creative writing
    - 🤔 Problem solving
    """)

# Display chat messages with enhanced formatting
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input with enhanced UX
if prompt := st.chat_input("Ask anything... 💭"):
    # Add user message
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)
    
    # Auto-save if enabled
    if auto_save:
        save_chat_history(st.session_state.messages)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response with enhanced error handling
    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        full_response = ""
        response_container = st.empty()
        
        try:
            # Show thinking indicator for free models that might be slower
            if is_free_model:
                with st.spinner(f"🤔 {model_names[selected_index]} is thinking..."):
                    time.sleep(0.5)  # Brief pause for UX
            
            for response in get_ai_response(st.session_state.messages, selected_model):
                full_response = response
                placeholder.markdown(full_response + "▌")
            
            # Remove cursor and finalize
            placeholder.markdown(full_response)
            
        except Exception as e:
            error_msg = f"💥 An unexpected error occurred: {str(e)}"
            placeholder.markdown(error_msg)
            full_response = error_msg
    
    # Add AI response to messages
    assistant_message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(assistant_message)
    
    # Auto-save if enabled
    if auto_save:
        save_chat_history(st.session_state.messages)

# Footer info
st.divider()
st.caption("💡 **Tip:** Free models (🆓) don't consume your API credits!")
st.caption(f"🤖 Currently using: **{model_names[selected_index]}**")