"""
Curriculum Manager - The RL Agent
Decides what the student should learn next based on their performance
"""
import numpy as np
import json
import os

class CurriculumManager:
    """
    A simple Contextual Bandit for curriculum adaptation
    State: (topic_mastery, last_quiz_score, sentiment)
    Actions: ['advance', 'review', 'quiz', 'easier']
    """
    
    def __init__(self, state_file="user_state.json"):
        self.state_file = state_file
        self.actions = ['advance', 'review', 'quiz', 'easier']
        
        # Q-table: action -> estimated reward
        # We use a simple epsilon-greedy strategy
        self.q_values = {action: 0.0 for action in self.actions}
        self.action_counts = {action: 0 for action in self.actions}
        self.epsilon = 0.2  # Exploration rate
        
        # Load existing state if available
        self.load_state()
        
    def get_action(self, student_state: dict) -> str:
        """
        Choose the next action based on student state
        student_state: {
            'topic_mastery': float (0-1),
            'last_quiz_score': int (0-100),
            'sentiment': str ('frustrated', 'neutral', 'happy')
        }
        """
        # Epsilon-greedy: explore vs exploit
        if np.random.random() < self.epsilon:
            # Explore: random action
            action = np.random.choice(self.actions)
        else:
            # Exploit: best action based on Q-values and state
            action = self._select_best_action(student_state)
            
        return action
    
    def _select_best_action(self, student_state: dict) -> str:
        """Select action based on heuristics and Q-values"""
        mastery = student_state.get('topic_mastery', 0.5)
        quiz_score = student_state.get('last_quiz_score', 50)
        sentiment = student_state.get('sentiment', 'neutral')
        
        # Rule-based heuristics combined with Q-values
        scores = {}
        
        for action in self.actions:
            score = self.q_values[action]
            
            # Adjust based on state
            if action == 'advance':
                if mastery > 0.7 and quiz_score > 70:
                    score += 10
                else:
                    score -= 5
                    
            elif action == 'review':
                if mastery < 0.5 or quiz_score < 60:
                    score += 10
                    
            elif action == 'quiz':
                if mastery > 0.4 and sentiment != 'frustrated':
                    score += 5
                    
            elif action == 'easier':
                if sentiment == 'frustrated' or quiz_score < 40:
                    score += 15
                    
            scores[action] = score
            
        # Return action with highest score
        return max(scores, key=scores.get)
    
    def update(self, action: str, reward: float):
        """
        Update Q-values based on reward
        Reward calculation:
        +10 for correct answer
        +5 for positive sentiment
        -5 for taking too long
        -10 for frustration
        """
        # Simple Q-learning update
        alpha = 0.1  # Learning rate
        
        self.action_counts[action] += 1
        self.q_values[action] += alpha * (reward - self.q_values[action])
        
        # Save state
        self.save_state()
        
    def save_state(self):
        """Save Q-values to file"""
        state = {
            'q_values': self.q_values,
            'action_counts': self.action_counts
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f)
            
    def load_state(self):
        """Load Q-values from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.q_values = state.get('q_values', self.q_values)
                    self.action_counts = state.get('action_counts', self.action_counts)
            except Exception as e:
                print(f"Could not load state: {e}")
