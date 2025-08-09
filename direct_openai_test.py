#!/usr/bin/env python3
"""
Direct OpenAI API test with the new key
"""

import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

async def test_openai_direct():
    """Test OpenAI API directly with the new key."""
    
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"🔑 Testing OpenAI API with key ending in: ...{api_key[-6:]}")
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        # Test with a very simple request
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheaper model
            messages=[
                {"role": "user", "content": "Say 'Hello' if you can read this."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        print("✅ OpenAI API Success!")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Tokens used: {response.usage.total_tokens}")
        print(f"Cost estimate: ${(response.usage.prompt_tokens * 0.0005 + response.usage.completion_tokens * 0.0015) / 1000:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_openai_direct())