#!/usr/bin/env python3
"""
Test API connections for OpenAI and Anthropic.
Run this after setting up your API keys to verify they work.
"""

import os
import asyncio
from dotenv import load_dotenv
import openai
from openai import AsyncOpenAI
import anthropic
from anthropic import AsyncAnthropic

async def test_openai_connection():
    """Test OpenAI API connection."""
    print("🤖 Testing OpenAI API Connection...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Say 'API connection test successful' if you can read this."}
            ],
            max_tokens=20,
            temperature=0
        )
        
        message = response.choices[0].message.content
        print(f"✅ OpenAI API: Connected successfully!")
        print(f"   Model: gpt-4o")
        print(f"   Response: {message}")
        print(f"   Usage: {response.usage.total_tokens} tokens")
        return True
        
    except openai.AuthenticationError:
        print("❌ OpenAI API: Authentication failed - check your API key")
        return False
    except openai.RateLimitError:
        print("⚠️  OpenAI API: Rate limit exceeded - try again later")
        return False
    except openai.APIError as e:
        print(f"❌ OpenAI API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error with OpenAI: {e}")
        return False

async def test_anthropic_connection():
    """Test Anthropic API connection."""
    print("\n🧠 Testing Anthropic API Connection...")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False
    
    try:
        client = AsyncAnthropic(api_key=api_key)
        
        # Test with a simple message
        response = await client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=20,
            temperature=0,
            messages=[
                {"role": "user", "content": "Say 'API connection test successful' if you can read this."}
            ]
        )
        
        message = response.content[0].text
        print(f"✅ Anthropic API: Connected successfully!")
        print(f"   Model: claude-3-opus-20240229")
        print(f"   Response: {message}")
        print(f"   Usage: {response.usage.input_tokens + response.usage.output_tokens} tokens")
        return True
        
    except anthropic.AuthenticationError:
        print("❌ Anthropic API: Authentication failed - check your API key")
        return False
    except anthropic.RateLimitError:
        print("⚠️  Anthropic API: Rate limit exceeded - try again later")
        return False
    except anthropic.APIError as e:
        print(f"❌ Anthropic API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error with Anthropic: {e}")
        return False

async def test_model_availability():
    """Test which models are available."""
    print("\n🔍 Testing Model Availability...")
    
    # Available OpenAI models for evaluation
    openai_models = [
        "gpt-4o",
        "gpt-4-turbo-preview",
        "gpt-4-0125-preview", 
        "gpt-3.5-turbo-0125"
    ]
    
    # Available Anthropic models
    anthropic_models = [
        "claude-3-5-sonnet-20241022",  # Latest
        "claude-3-opus-20240229",      # Deprecated Jan 2026
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]
    
    print(f"📋 Available OpenAI Models for Benchmark:")
    for model in openai_models:
        print(f"   • {model}")
    
    print(f"\n📋 Available Anthropic Models for Benchmark:")
    for model in anthropic_models:
        print(f"   • {model}")
    
    return openai_models, anthropic_models

def check_billing_setup():
    """Provide information about billing setup."""
    print("\n💳 Billing Setup Information:")
    print("=" * 40)
    print("🔸 OpenAI:")
    print("   • Set up billing: https://platform.openai.com/account/billing")
    print("   • Add payment method and usage limits")
    print("   • GPT-4 costs ~$30/1M input tokens, ~$60/1M output tokens")
    print()
    print("🔸 Anthropic:")
    print("   • Set up billing: https://console.anthropic.com/settings/billing")
    print("   • Add payment method and usage limits")
    print("   • Claude-3 Opus costs ~$15/1M input tokens, ~$75/1M output tokens")
    print()
    print("📊 Estimated benchmark costs:")
    print("   • 70 conversations × ~500 tokens each = ~35,000 tokens")
    print("   • Estimated cost per model: $1-3 USD")
    print("   • Total benchmark cost: $2-6 USD")

async def main():
    """Main test function."""
    print("🔑 API Connection Test")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Test connections
    openai_success = await test_openai_connection()
    anthropic_success = await test_anthropic_connection()
    
    # Test model availability
    await test_model_availability()
    
    # Billing information
    check_billing_setup()
    
    print("\n" + "=" * 40)
    if openai_success and anthropic_success:
        print("✅ All API connections successful!")
        print("\n🚀 Ready to run benchmark:")
        print("   python main.py --models gpt4 claude3 --trials 3")
    elif openai_success or anthropic_success:
        print("⚠️  Partial success - some APIs working")
        print("   You can run single-model benchmarks")
    else:
        print("❌ No API connections working")
        print("   Please check your API keys and billing setup")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")