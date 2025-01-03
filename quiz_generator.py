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
    Format the response as a JSON object with a 'questions' array where each question object has:
    {{
        "questions": [
            {{
                "question": "question text",
                "options": ["option1", "option2", "option3", "option4"],
                "correct_answer": "correct option text"
            }}
        ]
    }}
    Questions should test both theoretical knowledge and practical programming concepts."""

    try:
        # Initialize progress tracking
        progress_bar = st.progress(0)
        st.write("🤖 Initializing...")

        # Clear any previous error messages
        if 'error' in st.session_state:
            del st.session_state.error

        progress_bar.progress(20)
        st.write("⚡ Connecting to AI service...")

        # Create the API request with increased timeout
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert programming interviewer. Respond strictly in the requested JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=60  # Increased timeout to 60 seconds
        )

        progress_bar.progress(60)
        st.write("✨ Processing response...")

        # Parse and validate response
        try:
            response_content = response.choices[0].message.content
            response_json = json.loads(response_content)

            # Validate JSON structure
            if not isinstance(response_json, dict):
                raise ValueError("Response is not a JSON object")
            if "questions" not in response_json:
                raise ValueError("Response missing 'questions' array")
            if not isinstance(response_json["questions"], list):
                raise ValueError("'questions' is not an array")
            if len(response_json["questions"]) != 10:
                raise ValueError(f"Expected 10 questions, got {len(response_json['questions'])}")

            questions = response_json["questions"]

            # Validate each question
            for i, question in enumerate(questions):
                if not all(key in question for key in ["question", "options", "correct_answer"]):
                    raise ValueError(f"Question {i+1} missing required fields")
                if not isinstance(question["options"], list):
                    raise ValueError(f"Question {i+1} options is not an array")
                if len(question["options"]) != 4:
                    raise ValueError(f"Question {i+1} does not have exactly 4 options")
                if question["correct_answer"] not in question["options"]:
                    raise ValueError(f"Question {i+1} correct answer not in options")

            progress_bar.progress(100)
            st.write("✅ Questions ready!")
            return questions

        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format in API response: {str(e)}")
            return None
        except ValueError as e:
            st.error(f"Invalid response format: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Error processing response: {str(e)}")
            return None

    except Exception as e:
        st.error(f"Failed to generate questions: {str(e)}")
        st.warning("Please try again. If the problem persists, contact support.")
        return None