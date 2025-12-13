import csv
import os
from datetime import datetime

LOG_FILE = "session_logs.csv"

def log_interaction(user_id: str, interaction_type: str, input_data: str, output_data: str, sentiment: str, mastery: float, quiz_score: float):
    """
    Log user interaction to a CSV file for analysis.
    """
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write header if file is new
        if not file_exists:
            writer.writerow([
                "Timestamp", 
                "User_ID", 
                "Interaction_Type", 
                "Input", 
                "Output", 
                "Sentiment", 
                "Mastery_Level", 
                "Quiz_Score"
            ])
            
        # Write data row
        writer.writerow([
            datetime.now().isoformat(),
            user_id,
            interaction_type,
            input_data,
            output_data,
            sentiment,
            f"{mastery:.2f}",
            quiz_score
        ])
