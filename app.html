<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Chatbot</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f7f7f7;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .chatbot-container {
            width: 90%;
            max-width: 900px;
            height: 90vh;
            display: flex;
            flex-direction: column;
            background-color: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .chatbot-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 24px;
            border-bottom: 1px solid #e5e5e5;
        }

        .chatbot-logo {
            font-weight: 600;
            font-size: 1.25rem;
            color: #333;
        }

        .chatbot-info .status {
            color: #666;
            font-size: 0.8rem;
            margin-right: 10px;
        }

        .plus-button {
            background-color: #1a73e8;
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.8rem;
            cursor: pointer;
        }

        .chatbot-main {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 20px;
            overflow-y: auto;
        }

        .intro-message {
            max-width: 500px;
            margin-bottom: 20px;
            color: #444;
        }

        .intro-message h2 {
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .chat-area {
            width: 100%;
            max-width: 700px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            overflow-y: auto;
            padding: 20px 0;
        }

        .message {
            padding: 10px 15px;
            border-radius: 18px;
            max-width: 70%;
            word-wrap: break-word;
        }

        .user-message {
            background-color: #f0f0f0;
            align-self: flex-end;
        }

        .bot-message {
            background-color: #e6f7ff;
            align-self: flex-start;
        }

        .chatbot-input-form {
            padding: 16px 24px;
            border-top: 1px solid #e5e5e5;
        }

        .input-container {
            display: flex;
            border: 1px solid #e5e5e5;
            border-radius: 24px;
            padding: 8px;
            background-color: #f7f7f7;
        }

        #chat-input {
            flex-grow: 1;
            border: none;
            background: transparent;
            font-size: 1rem;
            padding: 0 10px;
        }

        #chat-input:focus {
            outline: none;
        }

        .send-button {
            background-color: #1a73e8;
            border: none;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
        }

        .send-button svg {
            fill: #fff;
            transform: rotate(45deg);
        }
    </style>
</head>
<body>
    <div class="chatbot-container">
        <header class="chatbot-header">
            <div class="chatbot-logo">ChatGPT</div>
            <div class="chatbot-info">
                <span class="status">Saved memory full</span>
                <button class="plus-button">+ Get Plus</button>
            </div>
        </header>

        <main class="chatbot-main">
            <div class="intro-message">
                <h2>Introducing GPT-5</h2>
                <p>ChatGPT now has our smartest, fastest, most useful model yet, with thinking built in — so you get the best answer, every time.</p>
            </div>
            <div class="chat-area">
                </div>
        </main>

        <form class="chatbot-input-form" id="chat-form">
            <div class="input-container">
                <input type="text" id="chat-input" placeholder="Ask anything" autocomplete="off">
                <button type="submit" class="send-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="text-white dark:text-black">
                        <path d="M12 4L3 9L12 14L21 9L12 4ZM12 16V22L21 9L12 16Z" fill="currentColor"></path>
                    </svg>
                </button>
            </div>
        </form>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const chatForm = document.getElementById('chat-form');
            const chatInput = document.getElementById('chat-input');
            const chatArea = document.querySelector('.chat-area');
            const introMessage = document.querySelector('.intro-message');

            // Replace with your OpenRouter API key
            const OPENROUTER_API_KEY = 'YOUR_OPENROUTER_API_KEY'; 

            const MODEL_NAME = 'gpt-3.5-turbo';

            const appendMessage = (message, sender) => {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message');
                messageDiv.classList.add(`${sender}-message`);
                messageDiv.textContent = message;
                chatArea.appendChild(messageDiv);
                chatArea.scrollTop = chatArea.scrollHeight;
            };

            const sendMessage = async (userMessage) => {
                // Hide the intro message when the first message is sent
                if (introMessage) {
                    introMessage.style.display = 'none';
                }

                appendMessage(userMessage, 'user');
                chatInput.value = '';

                try {
                    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            model: MODEL_NAME,
                            messages: [
                                { role: 'system', content: 'You are a helpful assistant.' },
                                { role: 'user', content: userMessage }
                            ],
                        }),
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error.message || `API error: ${response.statusText}`);
                    }

                    const data = await response.json();
                    const botMessage = data.choices[0].message.content;
                    appendMessage(botMessage, 'bot');

                } catch (error) {
                    console.error('Error:', error);
                    appendMessage('Sorry, I am unable to connect right now. Please try again later.', 'bot');
                }
            };

            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const userMessage = chatInput.value.trim();
                if (userMessage) {
                    sendMessage(userMessage);
                }
            });
        });
    </script>
</body>
</html>