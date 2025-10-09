#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')

print(f"API Key loaded: {api_key[:20]}...{api_key[-10:]}")
print(f"API Key length: {len(api_key)}")

# Test the API key
openai.api_key = api_key

try:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'API key works!'"}],
        max_tokens=10
    )
    print("\n✅ SUCCESS! API Key is working!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
