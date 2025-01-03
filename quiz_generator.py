import json
from openai import OpenAI
import os
import streamlit as st

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
        st.write("🤖 Connecting to AI service...")
        progress_bar = st.progress(0)

        # Create the API request with a timeout
        progress_bar.progress(25)
        st.write("⚡ Generating questions...")

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert programming interviewer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=30  # 30 seconds timeout
        )

        progress_bar.progress(75)
        st.write("✨ Processing response...")

        # Parse the response
        questions = json.loads(response.choices[0].message.content)["questions"]

        # Validate the questions format
        for question in questions:
            if not all(key in question for key in ["question", "options", "correct_answer"]):
                raise ValueError("Invalid question format in API response")
            if question["correct_answer"] not in question["options"]:
                raise ValueError("Correct answer not found in options")

        progress_bar.progress(100)
        st.write("✅ Questions ready!")
        return questions

    except Exception as e:
        st.error(f"Failed to generate questions: {str(e)}")
        st.warning("Please try again. If the problem persists, contact support.")
        return None