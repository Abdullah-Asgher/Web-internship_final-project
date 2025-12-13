import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Upgrade to error if no key
    print("FATAL: No API Key found.")
    exit(1)

genai.configure(api_key=api_key)

models_to_test = [
    "gemini-1.5-flash", 
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-lite-preview-02-05",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
    "gemini-pro"
]

print(f"Testing {len(models_to_test)} models with API Key ending in ...{api_key[-5:]}")
print("-" * 50)

working_model = None

for model_name in models_to_test:
    print(f"Testing: {model_name.ljust(35)}", end="", flush=True)
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, can you hear me?")
        if response and response.text:
            print("✅ SUCCESS!")
            working_model = model_name
            break # Stop at first working one to save time/quota
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            print("❌ 404 (Not Found)")
        elif "429" in error_str:
            print("❌ 429 (Quota Exceeded)")
        else:
            print(f"❌ Error: {error_str[:50]}...")

print("-" * 50)
if working_model:
    print(f"RECOMMENDATION: Use '{working_model}'")
else:
    print("FATAL: No working models found in the list.")
