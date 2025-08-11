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
    
    .model-id {
        color: #28a745;
        font-family: monospace;
    }
    
    .model-attribution {
        color: #28a745;
        font-size: 0.8em;
        font-style: italic;
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
    if not OPENROUTER_API_KEY:
        return "No API Key"
    try:
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        response = requests.get(url, headers=headers, timeout=10)
        return "Connected" if response.status_code == 200 else "Error"
    except:
        return "Error"

def get_ai_response(messages, model="openai/gpt-3.5-turbo"):
    if not OPENROUTER_API_KEY:
        return "No API key found. Please add OPENROUTER_API_KEY to environment variables."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8501",  # Optional: Your site URL
        "X-Title": "Streamlit AI Assistant"  # Optional: Your app name
    }
    
    # Create system message and user messages
    api_messages = [{"role": "system", "content": "You are a helpful AI assistant. Provide clear and helpful responses."}]
    api_messages.extend(messages)
    
    data = {
        "model": model,
        "messages": api_messages,
        "stream": True,
        "max_tokens": 2000,
        "temperature": 0.7,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=60)
        
        # Better error handling
        if response.status_code != 200:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
            except:
                error_detail = f"HTTP {response.status_code}: {response.reason}"
            
            yield f"API Error: {error_detail}. Please try a different model or check your API key."
            return
        
        full_response = ""
        buffer = ""
        
        # Using your working streaming logic
        for line in response.iter_lines():
            if line:
                # The server sends lines starting with "data: ..."
                if line.startswith(b"data: "):
                    data_str = line[len(b"data: "):].decode("utf-8")
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            full_response += delta
                            yield full_response
                    except json.JSONDecodeError:
                        continue
                    except (KeyError, IndexError):
                        continue
                            
    except requests.exceptions.Timeout:
        yield "Request timed out. Please try again with a shorter message or different model."
    except requests.exceptions.ConnectionError:
        yield "Connection error. Please check your internet connection and try again."
    except requests.exceptions.RequestException as e:
        yield f"Request error: {str(e)}. Please try again."
    except Exception as e:
        yield f"Unexpected error: {str(e)}. Please try again or contact support."

# Header
st.title("AI Assistant")
st.caption("Ask me anything")

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # API Status
    status = check_api_status()
    if status == "Connected":
        st.success("🟢 API Connected")
    elif status == "No API Key":
        st.error("No API Key")
    else:
        st.warning("Connection Issue")
    
    st.divider()
    
    # All models including new ones
    models = [
        ("GPT-3.5 Turbo", "openai/gpt-3.5-turbo"),
        ("LLaMA 3.1 8B", "meta-llama/llama-3.1-8b-instruct"),
        ("LLaMA 3.1 70B", "meta-llama/llama-3.1-70b-instruct"),
        ("DeepSeek Chat v3", "deepseek/deepseek-chat-v3-0324:free"),
        ("DeepSeek R1", "deepseek/deepseek-r1-0528:free"),
        ("Qwen3 Coder", "qwen/qwen3-coder:free"),
        ("Microsoft MAI DS R1", "microsoft/mai-ds-r1:free"),
        ("Gemma 3 27B", "google/gemma-3-27b-it:free"),
        ("Gemma 3 4B", "google/gemma-3-4b-it:free"),
        ("Auto (Best Available)", "openrouter/auto")
    ]
    
    model_names = [name for name, _ in models]
    model_ids = [model_id for _, model_id in models]
    
    selected_index = st.selectbox("Model", range(len(model_names)), 
                                format_func=lambda x: model_names[x], 
                                index=0)
    selected_model = model_ids[selected_index]
    
    # Show selected model ID in green
    st.markdown(f"**Model ID:** <span class='model-id'>{selected_model}</span>", unsafe_allow_html=True)
    
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
        try:
            for response in get_ai_response(st.session_state.messages, selected_model):
                full_response = response
                placeholder.markdown(full_response + "▌")
            
            # Remove cursor and show final response
            placeholder.markdown(full_response)
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            placeholder.markdown(error_msg)
            full_response = error_msg
    
    # Add AI response to messages with attribution
    full_response_with_attribution = full_response + f"\n\n---\n*Response created by: **{model_names[selected_index]}***"
    assistant_message = {"role": "assistant", "content": full_response_with_attribution}
    st.session_state.messages.append(assistant_message)
    
    # Auto-save if enabled
    if auto_save:
        save_chat_history(st.session_state.messages)

# Show currently using model
st.caption(f"Currently using: **{model_names[selected_index]}**")