"""
Tutor Agent - The conversational AI tutor
Combines RAG with sentiment analysis
"""
from app.core.rag import RAGSystem
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import re

class TutorAgent:
    def __init__(self):
        self.rag = RAGSystem()
        
        # Sentiment analysis LLM
        api_key = os.getenv("GOOGLE_API_KEY")
        self.sentiment_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.3
        )
        
    def respond(self, user_message: str, conversation_history: list = None) -> dict:
        """
        Generate a response to the user
        Returns: {
            'response': str,
            'sentiment': str ('frustrated', 'neutral', 'happy'),
            'sources': list
        }
        """
        # Build context from conversation history
        context = ""
        if conversation_history:
            context = "\n".join([
                f"{'Student' if msg.role == 'user' else 'Tutor'}: {msg.content}"
                for msg in conversation_history[-3:]  # Last 3 messages
            ])
        
        # Detect week context (Range or Single)
        filters = {}
        
        # Check for range "Week X to Y"
        range_match = re.search(r"(?:week|w)\s*(\d+)\s*(?:to|-|through)\s*(?:week|w)?\s*(\d+)", user_message, re.IGNORECASE)
        if range_match:
            try:
                start_week = int(range_match.group(1))
                end_week = int(range_match.group(2))
                week_list = list(range(start_week, end_week + 1))
                filters["week"] = {"$in": week_list}
                print(f"Detected context: Weeks {week_list}")
            except ValueError:
                pass
        else:
            # Check for single "Week X"
            week_match = re.search(r"(?:week|w)\s*(\d+)", user_message, re.IGNORECASE)
            if week_match:
                try:
                    week_num = int(week_match.group(1))
                    filters["week"] = week_num
                    print(f"Detected context: Week {week_num}")
                except ValueError:
                    pass

        # Get answer from RAG
        rag_response = self.rag.query(user_message, context, filters)
        
        # Detect sentiment
        sentiment = self._detect_sentiment(user_message)
        
        return {
            'response': rag_response['answer'],
            'sentiment': sentiment,
            'sources': rag_response['sources'],
            'in_knowledge_base': rag_response['in_knowledge_base']
        }
    
    def _detect_sentiment(self, message: str) -> str:
        """Detect user sentiment from their message using LLM"""
        # Use LLM for more accurate sentiment detection
        sentiment_prompt = f"""Analyze the sentiment of this student message. 
        
Student message: "{message}"

Classify the sentiment as EXACTLY one of these three options:
- frustrated (if the student seems confused, stuck, annoyed, or struggling)
- happy (if the student seems satisfied, grateful, or understanding well)
- neutral (if neither frustrated nor happy)

Respond with ONLY ONE WORD: frustrated, happy, or neutral"""

        try:
            response = self.rag.llm.invoke(sentiment_prompt)
            sentiment = response.content.strip().lower()
            
            # Validate response
            if sentiment in ['frustrated', 'happy', 'neutral']:
                return sentiment
            else:
                # Fallback to keyword-based if LLM gives unexpected response
                return self._keyword_sentiment(message)
        except Exception as e:
            print(f"Sentiment detection error: {e}")
            return self._keyword_sentiment(message)
    
    def _keyword_sentiment(self, message: str) -> str:
        """Fallback keyword-based sentiment detection"""
        message_lower = message.lower()
        
        frustrated_keywords = ['confused', 'don\'t understand', 'difficult', 'hard', 'frustrated', 'stuck', 
                              'why', 'what', 'how', 'explain', 'help', 'issue', 'problem', 'error']
        happy_keywords = ['thanks', 'got it', 'understand', 'clear', 'helpful', 'great', 'perfect', 
                         'awesome', 'excellent', 'good']
        
        if any(keyword in message_lower for keyword in frustrated_keywords):
            return 'frustrated'
        elif any(keyword in message_lower for keyword in happy_keywords):
            return 'happy'
        else:
            return 'neutral'
    
    def generate_quiz(self, topic: str) -> dict:
        """Generate a quiz question on a topic"""
        prompt = f"""Generate a multiple-choice quiz question about: {topic}

Format:
Question: [question text]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
Correct Answer: [A/B/C/D]
Explanation: [why this is correct]
"""
        
        response = self.sentiment_llm.invoke(prompt)
        return self._parse_quiz(response.content)
    
    def _parse_quiz(self, quiz_text: str) -> dict:
        """Parse the generated quiz into structured format"""
        lines = quiz_text.strip().split('\n')
        
        quiz = {
            'question': '',
            'options': {},
            'correct_answer': '',
            'explanation': ''
        }
        
        for line in lines:
            if line.startswith('Question:'):
                quiz['question'] = line.replace('Question:', '').strip()
            elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                option = line[0]
                text = line[2:].strip()
                quiz['options'][option] = text
            elif line.startswith('Correct Answer:'):
                quiz['correct_answer'] = line.replace('Correct Answer:', '').strip()
            elif line.startswith('Explanation:'):
                quiz['explanation'] = line.replace('Explanation:', '').strip()
                
        return quiz
