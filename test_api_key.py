
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("OPENROUTER_API_KEY", "")
print(f"API Key present: {bool(api_key)}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"API Key starts with: {api_key[:10]}..." if api_key else "No API key")

# Test basic import
try:
    from utils.openrouter_api import OPENROUTER_API_KEY
    print(f"Import successful, key length in module: {len(OPENROUTER_API_KEY)}")
    
    # Test actual API connection
    import requests
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    test_payload = {
        "model": "qwen/qwen-2.5-72b-instruct:free",
        "messages": [{"role": "user", "content": "Test"}],
        "max_tokens": 10
    }
    
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                           headers=headers, json=test_payload)
    print(f"API Test Response Status: {response.status_code}")
    if response.status_code != 200:
        print(f"API Error: {response.text}")
    else:
        print("✅ API connection successful!")
        
except Exception as e:
    print(f"Import/API error: {e}")")
