import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Get API key from env or use the one provided by user
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("API Key not found in env, using the one from user...")
    api_key = "AIzaSyBBm9vmZ8fMMgykgRUXarT-dAerJ84w51o"

print(f"Testing with API Key: {api_key[:10]}...")

try:
    print("Initializing ChatGoogleGenerativeAI with gemini-pro...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=api_key,
        temperature=0.7
    )
    
    print("Sending request...")
    response = llm.invoke([HumanMessage(content="Hello, are you working?")])
    print("Response received!")
    print(response.content)

except Exception as e:
    print(f"Error with gemini-pro: {e}")

print("-" * 20)

try:
    print("Initializing ChatGoogleGenerativeAI with gemini-1.5-flash...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.7
    )
    
    print("Sending request...")
    response = llm.invoke([HumanMessage(content="Hello, are you working?")])
    print("Response received!")
    print(response.content)

except Exception as e:
    print(f"Error with gemini-1.5-flash: {e}")
