import os
import sys
import traceback
from dotenv import load_dotenv

# Ensure backend path is in sys.path
sys.path.append(os.path.abspath("."))

load_dotenv()

try:
    from app.agents.tutor_agent import TutorAgent
    
    print("Initializing TutorAgent...")
    tutor = TutorAgent()
    
    class MockMessage:
        def __init__(self, role, content):
            self.role = role
            self.content = content
            
    history = [
        MockMessage("user", "Hello"),
        MockMessage("assistant", "Hi there!")
    ]
    
    print("Attempting to reproduce error with history...")
    response = tutor.respond("gimme the summary of week 6", conversation_history=history)
    
    print("Response received successfully:")
    print(response)

except Exception:
    print("CAUGHT EXCEPTION:")
    traceback.print_exc()
