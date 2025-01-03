import json
from openai import OpenAI
import os
import streamlit as st

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_first_question(language, difficulty):
    """Generate just the first question quickly"""
    prompt = f"""Generate 1 multiple choice question for a {difficulty} level {language} programming interview.
    The question should have 4 options with one correct answer.
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
    Question should test both theoretical knowledge and practical programming concepts."""

    try:
        # Initialize progress tracking
        progress_bar = st.progress(0)
        st.write("🤖 Generating first question...")

        # Clear any previous error messages
        if 'error' in st.session_state:
            del st.session_state.error

        progress_bar.progress(20)

        # Create the API request
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert programming interviewer. Respond strictly in the requested JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=30
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

            question = response_json["questions"][0]

            # Validate question structure
            if not all(key in question for key in ["question", "options", "correct_answer"]):
                raise ValueError("Question missing required fields")
            if not isinstance(question["options"], list):
                raise ValueError("Question options is not an array")
            if len(question["options"]) != 4:
                raise ValueError("Question does not have exactly 4 options")
            if question["correct_answer"] not in question["options"]:
                raise ValueError("Question correct answer not in options")

            progress_bar.progress(100)
            st.write("✅ First question ready!")
            return [question]

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
        st.error(f"Failed to generate question: {str(e)}")
        st.warning("Please try again. If the problem persists, contact support.")
        return None

def generate_remaining_questions(language, difficulty, first_question):
    """Generate the remaining 9 questions"""
    prompt = f"""Generate 9 more multiple choice questions for a {difficulty} level {language} programming interview.
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
        # Create the API request
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert programming interviewer. Respond strictly in the requested JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=60
        )

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

            # Combine with first question
            all_questions = first_question + questions
            return all_questions

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
        st.error(f"Failed to generate remaining questions: {str(e)}")
        st.warning("Please try again. If the problem persists, contact support.")
        return None

def generate_questions(language, difficulty):
    """Main function to generate all questions"""
    # First generate the initial question quickly
    first_question = generate_first_question(language, difficulty)
    if not first_question:
        return None

    # Then generate the remaining questions
    with st.spinner("Generating remaining questions..."):
        all_questions = generate_remaining_questions(language, difficulty, first_question)
        if all_questions and len(all_questions) == 10:
            return all_questions
        return None