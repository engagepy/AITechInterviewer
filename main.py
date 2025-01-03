import streamlit as st
import time
from quiz_generator import generate_questions
from analytics import generate_analytics
import json
import uuid
import pandas as pd
from datetime import datetime

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
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'answers' not in st.session_state:
        st.session_state.answers = []
    if 'times' not in st.session_state:
        st.session_state.times = []
    if 'notes' not in st.session_state:
        st.session_state.notes = []
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    if 'candidate_id' not in st.session_state:
        st.session_state.candidate_id = str(uuid.uuid4())[:8].upper()
    if 'profile_completed' not in st.session_state:
        st.session_state.profile_completed = False
    if 'candidate_info' not in st.session_state:
        st.session_state.candidate_info = {}

def reset_session():
    for key in st.session_state.keys():
        del st.session_state[key]
    initialize_session_state()

TECH_ROLES = {
    "Frontend Developer": {
        "languages": ["JavaScript", "TypeScript"],
        "difficulty": "Medium"
    },
    "Backend Developer": {
        "languages": ["Python", "Java", "Go"],
        "difficulty": "Hard"
    },
    "Full Stack Developer": {
        "languages": ["JavaScript", "Python", "Java"],
        "difficulty": "Hard"
    },
    "DevOps Engineer": {
        "languages": ["Python", "Go", "Shell"],
        "difficulty": "Medium"
    },
    "Mobile Developer": {
        "languages": ["Java", "Swift", "Kotlin"],
        "difficulty": "Medium"
    }
}

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

    if st.button("Begin Assessment", key="begin_assessment"):
        st.session_state.profile_completed = False
        st.rerun()

def collect_candidate_info():
    st.title("📝 Candidate Profile")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", key="name")
        age = st.number_input("Age", min_value=18, max_value=100, value=25, key="age")

    with col2:
        role = st.selectbox(
            "Position Applied For",
            options=list(TECH_ROLES.keys()),
            key="role"
        )

    if name and age and role:
        if st.button("Start Technical Interview"):
            st.session_state.candidate_info = {
                "name": name,
                "age": age,
                "role": role,
                "id": st.session_state.candidate_id,
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.profile_completed = True
            st.rerun()

def show_interview_page():
    role_info = TECH_ROLES[st.session_state.candidate_info["role"]]

    if not st.session_state.questions:
        st.title("🎯 Technical Assessment Configuration")

        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox(
                "Select Programming Language",
                options=role_info["languages"]
            )

        difficulty = role_info["difficulty"]
        with col2:
            st.info(f"Difficulty Level: {difficulty}")

        if st.button("Begin Interview"):
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

        with st.container():
            st.write(question["question"])

            selected_option = st.radio(
                "Select your answer:",
                question["options"],
                key=f"q_{st.session_state.current_question}"
            )

            notes = st.text_area(
                "Additional notes (optional):",
                key=f"notes_{st.session_state.current_question}"
            )

            col1, col2, col3 = st.columns([2,1,1])
            with col2:
                if st.button("Next Question" if st.session_state.current_question < 9 else "Finish Interview"):
                    st.session_state.answers.append(selected_option)
                    st.session_state.times.append(time.time() - st.session_state.start_time)
                    st.session_state.notes.append(notes)
                    st.session_state.start_time = time.time()

                    if st.session_state.current_question < 9:
                        st.session_state.current_question += 1
                    else:
                        st.session_state.quiz_completed = True
                    st.rerun()

def main():
    initialize_session_state()

    if not st.session_state.profile_completed:
        if 'quiz_completed' in st.session_state and st.session_state.quiz_completed:
            reset_session()
            show_welcome_page()
        else:
            if 'begin_assessment' not in st.session_state:
                show_welcome_page()
            else:
                collect_candidate_info()
    elif not st.session_state.quiz_completed:
        show_interview_page()
    else:
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

        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("Start New Interview"):
                reset_session()
                st.rerun()

if __name__ == "__main__":
    main()