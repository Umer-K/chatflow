def get_api_response(message: str) -> Optional[str]:
    """Get response from OpenRouter API with proper error handling"""
    if not API_ENABLED:
        return None
        
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://huggingface.co',
            },
            json={
                # EXPLICIT MODEL SPECIFICATION (Updated)
                'model': 'openai/gpt-3.5-turbo',  # Full provider/model path
                'messages': [{'role': 'user', 'content': message}],
                'temperature': 0.7,
                'max_tokens': 500,
            },
            timeout=15
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"API Error Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"API Error: {str(e)}")
        return None