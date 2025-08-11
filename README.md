ChatFlow 〽️
ChatFlow is a lightweight Streamlit-based AI assistant that connects to OpenRouter to give you access to multiple state-of-the-art language models. It features real-time streaming responses, persistent chat history, and a clean, distraction-free UI — making it ideal for both development and personal use.

🚀 Features
Multiple AI Models Support – Switch between GPT-3.5, LLaMA 3, DeepSeek, Qwen, Gemma, Microsoft MAI, or automatic best model via OpenRouter.

Streaming Responses – See answers appear in real time while they’re being generated.

Chat History Management – Save, load, clear, and download conversation history (chat_history.json).

Auto-Save Option – Automatically store messages between sessions.

Model Attribution – Shows which model produced each response.

Customizable Settings – Select model from the sidebar and check API connection status.

Persistent Storage – Keeps chat history even after restarting the app.

Minimalist UI – White background, hidden Streamlit menus, and compact layout.

Robust Error Handling – Detects API key issues, network errors, and timeouts.

📦 Installation
git clone https://github.com/Umer-K/chatflow.git
cd chatflow
pip install -r requirements.txt

🔑 Environment Variables
Set your OpenRouter API key before running the app:
export OPENROUTER_API_KEY="your_api_key_here"  # Linux / macOS
setx OPENROUTER_API_KEY "your_api_key_here"   # Windows

Get your API key from: https://openrouter.ai/keys

Use the sidebar to select the AI model and manage chat history.

Type your question in the chat input and receive a streaming AI response.

Save, load, or clear chat history directly from the sidebar.

📜 License
This project is licensed under the MIT License.
