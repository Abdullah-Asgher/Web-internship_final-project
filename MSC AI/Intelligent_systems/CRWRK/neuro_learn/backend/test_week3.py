import os
from dotenv import load_dotenv
load_dotenv()

from app.agents.tutor_agent import TutorAgent

print("Testing Week 3 Query...")
print(f"OpenAI Key found: {bool(os.getenv('OPENAI_API_KEY'))}")

tutor = TutorAgent()

try:
    response = tutor.respond("tell me about week 3", [])
    
    print("\n" + "="*50)
    print("RESPONSE:")
    print("="*50)
    print(response['response'][:500])
    print("\n" + "="*50)
    print("IN KNOWLEDGE BASE:", response['in_knowledge_base'])
    print("="*50)
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
