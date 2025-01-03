import streamlit as st
import time
from quiz_generator import generate_questions
from analytics import generate_analytics
import json

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

def reset_session():
    st.session_state.current_question = 0
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.times = []
    st.session_state.notes = []
    st.session_state.start_time = None
    st.session_state.quiz_completed = False

def main():
    st.title("AI Programming Interview Platform")
    
    initialize_session_state()
    
    if not st.session_state.quiz_completed:
        if not st.session_state.questions:
            col1, col2 = st.columns(2)
            with col1:
                language = st.selectbox(
                    "Select Programming Language",
                    ["Python", "JavaScript", "Java", "C++", "Ruby", "Go"]
                )
            with col2:
                difficulty = st.selectbox(
                    "Select Difficulty Level",
                    ["Easy", "Medium", "Hard"]
                )
            
            if st.button("Start Interview"):
                with st.spinner("Generating questions..."):
                    st.session_state.questions = generate_questions(language, difficulty)
                st.session_state.start_time = time.time()
                st.rerun()
        
        else:
            # Display current question
            question = st.session_state.questions[st.session_state.current_question]
            st.subheader(f"Question {st.session_state.current_question + 1}/10")
            st.write(question["question"])
            
            # Display options
            selected_option = st.radio(
                "Select your answer:",
                question["options"],
                key=f"q_{st.session_state.current_question}"
            )
            
            # Optional notes
            notes = st.text_area(
                "Additional notes (optional):",
                key=f"notes_{st.session_state.current_question}"
            )
            
            if st.button("Next Question" if st.session_state.current_question < 9 else "Finish Quiz"):
                # Record answer and time
                st.session_state.answers.append(selected_option)
                st.session_state.times.append(time.time() - st.session_state.start_time)
                st.session_state.notes.append(notes)
                st.session_state.start_time = time.time()
                
                if st.session_state.current_question < 9:
                    st.session_state.current_question += 1
                else:
                    st.session_state.quiz_completed = True
                st.rerun()
    
    else:
        # Show analytics
        st.success("Interview Completed!")
        generate_analytics(
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.times,
            st.session_state.notes
        )
        
        if st.button("Start New Interview"):
            reset_session()
            st.rerun()

if __name__ == "__main__":
    main()
