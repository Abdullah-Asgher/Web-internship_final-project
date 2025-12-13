import os
from dotenv import load_dotenv
load_dotenv()

from app.agents.tutor_agent import TutorAgent

print("Testing Week 6 Query...")
tutor = TutorAgent()

response = tutor.respond("gimme the summary of week 6", [])

print("\n" + "="*50)
print("RESPONSE:")
print("="*50)
print(response['response'])
print("\n" + "="*50)
print("SOURCES:")
print("="*50)
for source in response['sources'][:5]:
    if hasattr(source, 'metadata'):
        print(f"  - {source.metadata.get('source', 'Unknown')}")
    else:
        print(f"  - {source}")
