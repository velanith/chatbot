import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API
api_key = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    #"HTTP-Referer": "http://localhost:3000",  # Optional: your app URL
    #"X-Title": "Chatbot App"  # Optional: your app name
}

def query_chatbot(messages):
    payload = {
        "model": "gpt-oss-20b",
        "messages": messages,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text[:500]}")
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}")
    
    if not response.text.strip():
        raise Exception("Empty response from API")
    
    try:
        return response.json()
    except ValueError as e:
        raise Exception(f"Invalid JSON response: {response.text}")

chat_history = []

while True:
    user_input = input(">>User: ")
    
    # Add user message to chat history
    chat_history.append({"role": "user", "content": user_input})
    
    try:
        output = query_chatbot(chat_history)
        print(f"Raw output: {output}")
        
        if "choices" in output and len(output["choices"]) > 0:
            bot_response = output["choices"][0]["message"]["content"]
        else:
            bot_response = "No response"
            
        print(f"GPT-OSS: {bot_response}")
        
        # Add bot response to chat history
        chat_history.append({"role": "assistant", "content": bot_response})
        
    except Exception as e:
        print(f"Error: {e}")