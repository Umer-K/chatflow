import streamlit as st
import os
from openai import OpenAI
from streamlit.runtime.scriptrunner import add_script_run_ctx

# ==============================================================================
# 1. Page Configuration and Custom CSS
# ==============================================================================
# This section configures the page and injects custom CSS to style the app
# to look like the ChatGPT interface from your provided image.
# We're using Streamlit's wide layout and a custom title.

st.set_page_config(
    page_title="Streamlit Chat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match the ChatGPT aesthetic.
# We're styling the main content, the sidebar, chat messages, and the input box.
custom_css = """
<style>
    /* General body and background */
    body {
        background: linear-gradient(to right, #f7f7f7, #ffffff);
    }
    .stApp {
        background-color: transparent;
    }
    .main .block-container {
        max-width: 650px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Main chat area styling */
    .st-emotion-cache-18451p8 { /* This class targets the main content block */
        background-color: transparent;
        padding: 0 1rem;
    }

    /* Sidebar styling */
    .st-emotion-cache-12fmj92 {
        background-color: #202123;
        color: #f7f7f7;
    }
    .st-emotion-cache-12fmj92 a {
        color: #f7f7f7;
    }
    .st-emotion-cache-12fmj92 .stButton button {
        background-color: transparent;
        border: 1px solid #d9d9e3;
        color: #f7f7f7;
    }
    .st-emotion-cache-12fmj92 .stButton button:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }

    /* Chat message styling to mimic ChatGPT */
    .st-emotion-cache-gftf1k {
        background-color: #f7f7f7;
        border-radius: 10px;
        padding: 10px;
    }
    .st-emotion-cache-199v41 {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
    }

    /* Header for the chat page */
    .st-emotion-cache-1629p8f h1 {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .st-emotion-cache-1629p8f p {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-bottom: 3rem;
    }

    /* Chat input box styling to match the image */
    .st-emotion-cache-10qg19x {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        margin: 0 auto;
        max-width: 650px;
        padding: 1rem;
        background: linear-gradient(to right, #f7f7f7, #ffffff);
        z-index: 100;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
    .st-emotion-cache-10qg19x .st-emotion-cache-1n1p154 {
        border-radius: 20px;
        border: 1px solid #d9d9e3;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        padding: 10px;
    }
    .st-emotion-cache-10qg19x input {
        border: none;
        outline: none;
    }
    .st-emotion-cache-10qg19x label {
        display: none;
    }
    .st-emotion-cache-10qg19x .st-emotion-cache-1e5x6cs {
        background-color: transparent;
        border-radius: 20px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# ==============================================================================
# 2. OpenRouter API Configuration and Client
# ==============================================================================
# This section sets up the connection to the OpenRouter API.
# It's important to use st.secrets for secure credential management.
# The user will need to add their API key to a secrets.toml file.
# The client is configured to use OpenRouter's specific base URL.

try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("OpenRouter API key not found. Please set it in your secrets.toml file.")
    st.stop()

# Initialize the OpenAI client with the OpenRouter API base URL.
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)


# ==============================================================================
# 3. Sidebar Navigation
# ==============================================================================
# Recreating the sidebar from the ChatGPT UI with placeholders.
# This section shows how you can structure a multi-page app or navigation.

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/1200px-ChatGPT_logo.svg.png", width=30)
    st.title("ChatGPT")
    st.button("New Chat", key="new_chat_button")
    st.divider()

    st.subheader("Your chats")
    st.markdown("- Chat about Streamlit")
    st.markdown("- Brainstorming ideas")

    st.divider()
    st.markdown("💬 **Saved memory full**")
    st.markdown("[✨ Get Plus](https://chat.openai.com/gpts)")


# ==============================================================================
# 4. Main Chat Interface
# ==============================================================================
# This is the core of the application where the chat history is managed and
# displayed, and where the user can interact with the chatbot.

st.title("Introducing GPT-5")
st.caption("ChatGPT now has our smartest, fastest, most useful model yet, with thinking built in—so you get the best answer, every time.")


# Initialize chat history in session state if it doesn't exist.
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display chat messages from history on app rerun.
# We iterate through the messages stored in st.session_state.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept user input.
# The prompt is handled by st.chat_input, which is located at the bottom of the page.
if prompt := st.chat_input("Ask anything"):
    # Add user message to chat history.
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container.
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display assistant response.
    # The response is streamed from the API to provide a dynamic user experience.
    with st.chat_message("assistant"):
        # Create a placeholder to display the streamed response.
        response_placeholder = st.empty()
        full_response = ""
        
        # Use a try-except block to handle potential API errors gracefully.
        try:
            # Make the API call to OpenRouter.
            # We are using the 'gpt-3.5-turbo' model as requested.
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )

            # Iterate through the streamed response and append chunks.
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response)
        
        except Exception as e:
            # Display a user-friendly error message if the API call fails.
            error_message = f"An error occurred: {e}"
            response_placeholder.error(error_message)
            full_response = error_message
            st.stop()

    # Add assistant response to chat history.
    st.session_state.messages.append({"role": "assistant", "content": full_response})

