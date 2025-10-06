"""
Simple test for your Gemini API key
"""
import requests

API_KEY = "AIzaSyAivQg8d1g-fLn98PbzQ8poXc2EKFb-1kE"

print("Testing Gemini API Key...")
print("=" * 60)

# Models to test (Google AI Studio compatible)
models = [
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash", 
    "gemini-1.5-pro",
    "gemini-pro"
]

test_prompt = "Say hello in one sentence."

for model in models:
    print(f"\n🔍 Testing: {model}")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": test_prompt
            }]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"   ✅ SUCCESS!")
                print(f"   Response: {text}")
                print(f"\n{'='*60}")
                print(f"✨ WORKING MODEL: {model}")
                print(f"{'='*60}")
                break
        else:
            print(f"   ❌ Failed: {response.text[:150]}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("TIP: If all failed, check:")
print("1. Go to: https://aistudio.google.com/app/apikey")
print("2. Create a NEW API key")
print("3. Replace in your .env file")
print("=" * 60)