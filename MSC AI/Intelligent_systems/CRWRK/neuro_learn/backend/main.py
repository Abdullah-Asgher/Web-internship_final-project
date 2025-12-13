"""
FastAPI Server for NeuroLearn
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from app.agents.tutor_agent import TutorAgent
from app.agents.curriculum_manager import CurriculumManager
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="NeuroLearn API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
tutor = TutorAgent()
curriculum_manager = CurriculumManager()

# User session storage (in production, use a database)
user_sessions = {}

# Pydantic models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    response: str
    sentiment: str
    next_action: str
    sources: List[dict] = []

class QuizRequest(BaseModel):
    topic: str

class FeedbackRequest(BaseModel):
    user_id: str
    action: str
    correct: bool
    time_taken: float
    sentiment: str

@app.get("/")
async def root():
    return {"message": "NeuroLearn API is running!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        # Get or create user session
        if request.user_id not in user_sessions:
            user_sessions[request.user_id] = {
                'topic_mastery': 0.5,
                'last_quiz_score': 50,
                'sentiment': 'neutral',
                'conversation_history': []
            }
        
        session = user_sessions[request.user_id]
        
        # Get tutor response
        tutor_response = tutor.respond(
            request.message,
            request.conversation_history
        )
        
        # Update session sentiment
        session['sentiment'] = tutor_response['sentiment']
        
        # Get next action from curriculum manager
        next_action = curriculum_manager.get_action(session)
        
        # Update conversation history
        session['conversation_history'].append({
            'role': 'user',
            'content': request.message
        })
        session['conversation_history'].append({
            'role': 'assistant',
            'content': tutor_response['response']
        })
        
        # Log interaction
        from app.core.logger import log_interaction
        log_interaction(
            user_id=request.user_id,
            interaction_type="chat",
            input_data=request.message,
            output_data=tutor_response['response'][:100] + "...", # Truncate for log
            sentiment=tutor_response['sentiment'],
            mastery=session['topic_mastery'],
            quiz_score=session['last_quiz_score']
        )

        return ChatResponse(
            response=tutor_response['response'],
            sentiment=tutor_response['sentiment'],
            next_action=next_action,
            sources=[{
                'content': doc.page_content[:200],
                'source': os.path.basename(doc.metadata.get('source', 'Unknown')),
                'page': doc.metadata.get('page', 'N/A')
            } for doc in tutor_response['sources'][:3]]
        )
        
    except ValueError as e:
        # Handle specific validation errors
        error_msg = "I had trouble understanding your question. Could you please rephrase it?"
        print(f"ValueError in /chat endpoint: {str(e)}")
        return ChatResponse(
            response=error_msg,
            sentiment="neutral",
            next_action="continue",
            sources=[]
        )
    except Exception as e:
        # Catch-all for any errors - never show technical details to students
        error_msg = "I apologize, but I encountered a temporary issue. Please try asking your question again."
        print(f"ERROR in /chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            response=error_msg,
            sentiment="neutral",
            next_action="continue",
            sources=[]
        )

@app.post("/quiz")
async def generate_quiz(request: QuizRequest):
    """Generate a quiz question"""
    try:
        quiz = tutor.generate_quiz(request.topic)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback to update the RL agent"""
    try:
        # Calculate reward
        reward = 0
        if request.correct:
            reward += 10
        if request.sentiment == 'happy':
            reward += 5
        elif request.sentiment == 'frustrated':
            reward -= 10
        if request.time_taken > 60:  # More than 1 minute
            reward -= 5
            
        # Update curriculum manager
        curriculum_manager.update(request.action, reward)
        
        # Update user session
        if request.user_id in user_sessions:
            session = user_sessions[request.user_id]
            if request.correct:
                session['topic_mastery'] = min(1.0, session['topic_mastery'] + 0.1)
                session['last_quiz_score'] = min(100, session['last_quiz_score'] + 10)
            else:
                session['topic_mastery'] = max(0.0, session['topic_mastery'] - 0.05)
                session['last_quiz_score'] = max(0, session['last_quiz_score'] - 5)
                
            # Log feedback
            from app.core.logger import log_interaction
            log_interaction(
                user_id=request.user_id,
                interaction_type="feedback",
                input_data=f"Action: {request.action}, Correct: {request.correct}",
                output_data=f"Reward: {reward}",
                sentiment=request.sentiment,
                mastery=session['topic_mastery'],
                quiz_score=session['last_quiz_score']
            )
        
        return {"status": "success", "reward": reward}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get user learning statistics"""
    if user_id not in user_sessions:
        return {"error": "User not found"}
    
    session = user_sessions[user_id]
    return {
        'topic_mastery': session['topic_mastery'],
        'last_quiz_score': session['last_quiz_score'],
        'sentiment': session['sentiment'],
        'total_messages': len(session['conversation_history'])
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
