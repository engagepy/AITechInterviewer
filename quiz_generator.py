import json
from openai import OpenAI
import os

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_questions(language, difficulty):
    prompt = f"""Generate 10 multiple choice questions for a {difficulty} level {language} programming interview.
    Each question should have 4 options with one correct answer.
    Format the response as a JSON array where each question object has the following structure:
    {{
        "question": "question text",
        "options": ["option1", "option2", "option3", "option4"],
        "correct_answer": "correct option text"
    }}
    Questions should test both theoretical knowledge and practical programming concepts."""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert programming interviewer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        questions = json.loads(response.choices[0].message.content)["questions"]
        return questions
    except Exception as e:
        raise Exception(f"Failed to generate questions: {e}")
