import streamlit as st
import time
from quiz_generator import generate_questions
from analytics import generate_analytics
import json
import uuid
import pandas as pd
from datetime import datetime
import PyPDF2
import io
import os
from openai import OpenAI

# Initialize OpenAI client
openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="AI-Powered Technical Interview Platform",
    page_icon="🤖",
    layout="wide"
)

# Load custom CSS
with open(".streamlit/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'current_question': 0,
        'questions': [],
        'answers': [],
        'times': [],
        'notes': [],
        'start_time': None,
        'quiz_completed': False,
        'candidate_id': str(uuid.uuid4())[:8].upper(),
        'profile_completed': False,
        'candidate_info': {},
        'cv_uploaded': False,
        'suggested_role': None,
        'page': 'welcome'  # New state variable to track current page
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_session():
    """Reset all session state variables"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session_state()

# Tech roles configuration
TECH_ROLES = {
    "Frontend Developer": {
        "languages": ["JavaScript", "TypeScript"],
        "difficulty": "Medium",
        "keywords": ["react", "angular", "vue", "html", "css", "frontend", "ui", "ux"]
    },
    "Backend Developer": {
        "languages": ["Python", "Java", "Go"],
        "difficulty": "Hard",
        "keywords": ["backend", "api", "database", "server", "django", "spring", "golang"]
    },
    "Full Stack Developer": {
        "languages": ["JavaScript", "Python", "Java"],
        "difficulty": "Hard",
        "keywords": ["fullstack", "full-stack", "frontend", "backend", "web"]
    },
    "DevOps Engineer": {
        "languages": ["Python", "Go", "Shell"],
        "difficulty": "Medium",
        "keywords": ["devops", "ci/cd", "aws", "docker", "kubernetes", "infrastructure"]
    },
    "Mobile Developer": {
        "languages": ["Java", "Swift", "Kotlin"],
        "difficulty": "Medium",
        "keywords": ["mobile", "android", "ios", "react native", "flutter"]
    }
}

def analyze_cv(cv_content):
    """Analyze CV content and suggest a role"""
    try:
        prompt = f"""Analyze this CV and suggest the most appropriate technical role from the following options: {', '.join(TECH_ROLES.keys())}.
        Consider the candidate's experience, skills, and technologies mentioned.
        CV Content:
        {cv_content}

        Respond in JSON format with:
        {{
            "suggested_role": "one of the roles listed above",
            "confidence": "score between 0 and 1",
            "reasoning": "brief explanation for the suggestion"
        }}
        """

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error analyzing CV: {str(e)}")
        return None

def extract_text_from_pdf(pdf_bytes):
    """Extract text content from uploaded PDF"""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def show_welcome_page():
    st.title("🚀 Welcome to AI-Powered Technical Interview Platform")

    st.markdown("""
    ### Transform Your Technical Hiring Process

    Our cutting-edge AI-powered platform revolutionizes technical interviews by:
    - 🤖 Leveraging advanced AI to generate tailored questions
    - 📊 Providing real-time analytics and insights
    - 🎯 Ensuring fair and consistent evaluation
    - ⏱️ Saving time and resources in the hiring process

    Let's get started with your technical assessment!
    """)

    if st.button("Begin Assessment"):
        st.session_state.page = 'profile'
        st.rerun()

def collect_candidate_info():
    st.title("📝 Candidate Profile")

    # Create a form for better submission handling
    with st.form("candidate_profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Full Name", key="form_name")
            age = st.number_input("Age", min_value=18, max_value=100, value=25, key="form_age")

            # CV Upload
            uploaded_file = st.file_uploader("Upload your CV (PDF)", type=['pdf'])

        with col2:
            role = st.selectbox(
                "Position Applied For",
                options=list(TECH_ROLES.keys()),
                index=list(TECH_ROLES.keys()).index(st.session_state.suggested_role) if st.session_state.suggested_role else 0,
                key="form_role"
            )

            if st.session_state.suggested_role and role != st.session_state.suggested_role:
                st.info("Note: You've selected a different role than suggested based on your CV.")

        # Submit button must be the last element in the form
        submitted = st.form_submit_button("Start Technical Interview")

        if submitted and name and age and role:
            if uploaded_file is not None and not st.session_state.cv_uploaded:
                cv_content = extract_text_from_pdf(uploaded_file.getvalue())
                if cv_content:
                    with st.spinner("Analyzing your CV..."):
                        analysis = analyze_cv(cv_content)
                        if analysis:
                            st.session_state.suggested_role = analysis["suggested_role"]
                            st.session_state.cv_uploaded = True
                            st.success(f"CV Analysis Complete! Suggested Role: {analysis['suggested_role']}")
                            st.info(f"Reasoning: {analysis['reasoning']}")

            st.session_state.candidate_info = {
                "name": name,
                "age": age,
                "role": role,
                "id": st.session_state.candidate_id,
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.profile_completed = True
            st.session_state.page = 'interview'
            st.rerun()

def show_interview_page():
    role_info = TECH_ROLES[st.session_state.candidate_info["role"]]

    if not st.session_state.questions:
        st.title("🎯 Technical Assessment Configuration")

        with st.form("interview_config_form"):
            col1, col2 = st.columns(2)
            with col1:
                language = st.selectbox(
                    "Select Programming Language",
                    options=role_info["languages"]
                )

            difficulty = role_info["difficulty"]
            with col2:
                st.info(f"Difficulty Level: {difficulty}")

            if st.form_submit_button("Begin Interview"):
                with st.spinner("Preparing your technical assessment..."):
                    st.session_state.questions = generate_questions(language, difficulty)
                st.session_state.start_time = time.time()
                st.rerun()

    else:
        # Progress bar
        progress = (st.session_state.current_question) / len(st.session_state.questions)
        st.progress(progress)

        # Question display
        question = st.session_state.questions[st.session_state.current_question]

        st.subheader(f"Question {st.session_state.current_question + 1}/10")

        with st.form(f"question_form_{st.session_state.current_question}"):
            st.write(question["question"])

            selected_option = st.radio(
                "Select your answer:",
                question["options"]
            )

            notes = st.text_area(
                "Additional notes (optional):"
            )

            if st.form_submit_button("Next Question" if st.session_state.current_question < 9 else "Finish Interview"):
                st.session_state.answers.append(selected_option)
                st.session_state.times.append(time.time() - st.session_state.start_time)
                st.session_state.notes.append(notes)
                st.session_state.start_time = time.time()

                if st.session_state.current_question < 9:
                    st.session_state.current_question += 1
                else:
                    st.session_state.quiz_completed = True
                    st.session_state.page = 'results'
                st.rerun()

def show_results_page():
    st.title("📊 Assessment Results")

    # Display candidate information
    st.sidebar.success(f"""
    ### Candidate Information
    **ID:** {st.session_state.candidate_info['id']}
    **Name:** {st.session_state.candidate_info['name']}
    **Role:** {st.session_state.candidate_info['role']}
    **Date:** {st.session_state.candidate_info['datetime']}
    """)

    # Generate and display analytics
    generate_analytics(
        st.session_state.questions,
        st.session_state.answers,
        st.session_state.times,
        st.session_state.notes,
        st.session_state.candidate_info
    )

    if st.button("Start New Interview"):
        reset_session()
        st.rerun()

def main():
    initialize_session_state()

    # Page routing based on session state
    if st.session_state.page == 'welcome':
        show_welcome_page()
    elif st.session_state.page == 'profile':
        collect_candidate_info()
    elif st.session_state.page == 'interview':
        show_interview_page()
    elif st.session_state.page == 'results':
        show_results_page()

if __name__ == "__main__":
    main()