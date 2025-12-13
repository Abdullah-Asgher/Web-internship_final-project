import os
import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("API Key not found in env, using the one from user...")
    api_key = "AIzaSyBBm9vmZ8fMMgykgRUXarT-dAerJ84w51o"

print(f"Configuring with API Key: {api_key[:10]}...")
genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
