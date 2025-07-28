#!/usr/bin/env python3
"""
OpenRouter Connection Diagnostic Script
This script tests various aspects of your OpenRouter connection to identify 502 gateway issues.
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_basic_connectivity():
    """Test basic connectivity to OpenRouter"""
    print("=== Testing Basic Connectivity ===")
    try:
        response = requests.get("https://openrouter.ai", timeout=10)
        print(f"✓ OpenRouter website accessible: {response.status_code}")
        return True
    except Exception as e:
        print(f"✗ Cannot reach OpenRouter website: {e}")
        return False

def test_api_endpoint():
    """Test API endpoint availability"""
    print("\n=== Testing API Endpoint ===")
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        print(f"✓ API endpoint accessible: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"✓ Found {len(models.get('data', []))} available models")
        return True
    except Exception as e:
        print(f"✗ Cannot reach API endpoint: {e}")
        return False

def test_api_key():
    """Test API key validation"""
    print("\n=== Testing API Key ===")
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("✗ OPENROUTER_API_KEY not found in environment variables")
        return False

    print(f"✓ API key found: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")

    # Test API key with a simple request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get("https://openrouter.ai/api/v1/models",
                              headers=headers, timeout=10)
        if response.status_code == 200:
            print("✓ API key is valid")
            return True
        elif response.status_code == 401:
            print("✗ API key is invalid or expired")
            return False
        else:
            print(f"✗ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error testing API key: {e}")
        return False

def test_model_availability():
    """Test if the specific model you're using is available"""
    print("\n=== Testing Model Availability ===")
    api_key = os.getenv("OPENROUTER_API_KEY")
    model_name = "google/gemini-2.5-flash-lite"

    if not api_key:
        print("✗ Cannot test model without API key")
        return False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get("https://openrouter.ai/api/v1/models",
                              headers=headers, timeout=10)
        if response.status_code == 200:
            models = response.json()
            model_ids = [model['id'] for model in models.get('data', [])]

            if model_name in model_ids:
                print(f"✓ Model '{model_name}' is available")
                return True
            else:
                print(f"✗ Model '{model_name}' not found")
                print("Available models with 'gemini' in name:")
                gemini_models = [m for m in model_ids if 'gemini' in m.lower()]
                for model in gemini_models[:5]:  # Show first 5
                    print(f"  - {model}")
                return False
        else:
            print(f"✗ Cannot retrieve models: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error checking model availability: {e}")
        return False

def test_chat_completion():
    """Test actual chat completion request"""
    print("\n=== Testing Chat Completion ===")
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("✗ Cannot test without API key")
        return False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",  # Optional: helps with rate limiting
        "X-Title": "Study.io Backend Service"     # Optional: helps identify your app
    }

    payload = {
        "model": "google/gemini-2.5-flash-lite",
        "messages": [
            {
                "role": "user",
                "content": "Generate one simple flashcard about Python. Return JSON with 'front' and 'back' keys."
            }
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    try:
        print("Making test request...")
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                               headers=headers,
                               json=payload,
                               timeout=30)

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✓ Chat completion successful!")
            content = result['choices'][0]['message']['content']
            print(f"Response content: {content[:100]}...")
            return True
        elif response.status_code == 502:
            print("✗ 502 Bad Gateway - This is the error you're experiencing!")
            print("Response headers:", dict(response.headers))
            print("Response text:", response.text)
            return False
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print("Response text:", response.text)
            return False

    except requests.exceptions.Timeout:
        print("✗ Request timed out - server may be overloaded")
        return False
    except Exception as e:
        print(f"✗ Error making request: {e}")
        return False

def test_with_different_models():
    """Test with alternative models to see if it's model-specific"""
    print("\n=== Testing Alternative Models ===")
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("✗ Cannot test without API key")
        return False

    # Alternative free models to try
    test_models = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "google/gemma-2-9b-it:free"
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for model in test_models:
        print(f"\nTesting model: {model}")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello, respond with just 'OK'"}],
            "max_tokens": 10
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                   headers=headers,
                                   json=payload,
                                   timeout=15)

            if response.status_code == 200:
                print(f"✓ {model} works!")
                return True
            else:
                print(f"✗ {model} failed: {response.status_code}")
        except Exception as e:
            print(f"✗ {model} error: {e}")

    return False

def main():
    """Run all diagnostic tests"""
    print("OpenRouter Connection Diagnostic")
    print("=" * 40)

    tests = [
        test_basic_connectivity,
        test_api_endpoint,
        test_api_key,
        test_model_availability,
        test_chat_completion,
        test_with_different_models
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append(False)

        time.sleep(1)  # Brief pause between tests

    print("\n" + "=" * 40)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 40)

    if all(results):
        print("✓ All tests passed - your OpenRouter connection should be working")
    else:
        print("✗ Some tests failed - see details above")

        if not results[0]:
            print("- Network connectivity issue")
        if not results[1]:
            print("- OpenRouter API endpoint issue")
        if not results[2]:
            print("- API key issue")
        if not results[3]:
            print("- Model availability issue")
        if not results[4]:
            print("- Chat completion issue (this is your 502 error)")
        if not results[5]:
            print("- All models failing")

if __name__ == "__main__":
    main()
