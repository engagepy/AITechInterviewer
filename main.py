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
    page_icon="🚀",
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
        "languages": ["JavaScript", "TypeScript", "React", "Angular", "Vue.js"],
        "difficulty": "Medium",
        "keywords": ["react", "angular", "vue", "html", "css", "frontend", "ui", "ux"]
    },
    "Backend Developer": {
        "languages": ["Python", "Java", "Go", "Node.js", "Ruby"],
        "difficulty": "Hard",
        "keywords": ["backend", "api", "database", "server", "django", "spring", "golang"]
    },
    "Full Stack Developer": {
        "languages": ["JavaScript", "Python", "Java", "TypeScript", "PHP"],
        "difficulty": "Hard",
        "keywords": ["fullstack", "full-stack", "frontend", "backend", "web"]
    },
    "DevOps Engineer": {
        "languages": ["Python", "Go", "Shell", "Ruby", "JavaScript"],
        "difficulty": "Medium",
        "keywords": ["devops", "ci/cd", "aws", "docker", "kubernetes", "infrastructure"]
    },
    "Mobile Developer": {
        "languages": ["Java", "Swift", "Kotlin", "React Native", "Flutter"],
        "difficulty": "Medium",
        "keywords": ["mobile", "android", "ios", "react native", "flutter"]
    },
    "Product Manager": {
        "languages": ["Agile", "Scrum", "Kanban", "Product Strategy", "User Stories"],
        "difficulty": "Medium",
        "keywords": ["product", "agile", "scrum", "jira", "miro", "roadmap", "user stories", "backlog"]
    },
    "Salesforce Developer": {
        "languages": ["Apex", "Lightning Web Components", "Visualforce", "SOQL", "JavaScript"],
        "difficulty": "Medium",
        "keywords": ["salesforce", "apex", "lwc", "visualforce", "soql", "crm"]
    },
    "AWS Cloud Engineer": {
        "languages": ["Python", "Shell", "CloudFormation", "Terraform", "AWS CLI"],
        "difficulty": "Hard",
        "keywords": ["aws", "cloud", "ec2", "s3", "lambda", "cloudformation", "terraform"]
    }
}

def analyze_cv(cv_content):
    """Analyze CV content and suggest a role"""
    try:
        prompt = f"""Analyze this CV and extract the following information:
        1. The candidate's full name from the CV
        2. The most appropriate technical role from these options: {', '.join(TECH_ROLES.keys())}
        3. Consider the candidate's experience, skills, and technologies mentioned.
        4. For the selected role, identify the most relevant programming languages or tools.

        CV Content:
        {cv_content}

        Respond in JSON format with:
        {{
            "candidate_name": "full name from CV",
            "suggested_role": "one of the roles listed above",
            "confidence": "score between 0 and 1",
            "reasoning": "brief explanation for the suggestion",
            "recommended_languages": ["list", "of", "relevant", "languages"],
            "years_of_experience": "estimated years of experience"
        }}
        """

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        analysis = json.loads(response.choices[0].message.content)

        # Filter languages based on the suggested role
        role_languages = TECH_ROLES[analysis["suggested_role"]]["languages"]
        analysis["recommended_languages"] = [lang for lang in analysis["recommended_languages"] if lang in role_languages]

        return analysis
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
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Title and subtitle
    st.title("🚀 AI-Powered Technical Interview Platform")
    st.markdown("<p class='subtitle'>Experience the future of technical assessments with our cutting-edge AI platform.</p>", unsafe_allow_html=True)

    # Begin Assessment Button
    if st.button("BEGIN ASSESSMENT", use_container_width=True):
        st.session_state.page = 'profile'
        st.rerun()

    # Features section using columns
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>Real-time Analytics</h3>
            <p>Comprehensive performance metrics and detailed insights</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3>Tailored Assessment</h3>
            <p>Dynamic question generation based on expertise and experience</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">✨</div>
            <h3>Instant Feedback</h3>
            <p>Detailed reports and recommendations for improvement</p>
        </div>
        """, unsafe_allow_html=True)

    # Roles section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="roles-section">
        <h2>Expert assessment for multiple technical positions including:</h2>
        <ul>
            <li>Frontend, Backend, and Full Stack Developers</li>
            <li>DevOps and Cloud Engineers</li>
            <li>Product Managers</li>
            <li>Salesforce Developers</li>
            <li>Mobile Developers</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def collect_candidate_info():
    st.title("📝 Candidate Profile")

    col1, col2 = st.columns(2)

    with col1:
        # Keep CV upload outside the form as it needs to trigger immediate analysis
        uploaded_file = st.file_uploader("Upload your CV (PDF)", type=['pdf'])
        if uploaded_file is not None and not st.session_state.cv_uploaded:
            cv_content = extract_text_from_pdf(uploaded_file.getvalue())
            if cv_content:
                with st.spinner("Analyzing your CV..."):
                    analysis = analyze_cv(cv_content)
                    if analysis:
                        st.session_state.candidate_name = analysis["candidate_name"]
                        st.session_state.suggested_role = analysis["suggested_role"]
                        st.session_state.recommended_languages = analysis["recommended_languages"]
                        st.session_state.cv_uploaded = True

                        # Parse years of experience
                        try:
                            exp_str = analysis['years_of_experience'].lower().split()[0]
                            if '-' in exp_str:
                                low, high = map(float, exp_str.split('-'))
                                years = (low + high) / 2
                            else:
                                years = float(exp_str)

                            if years < 1:
                                difficulty = "Easy"
                            elif years < 3:
                                difficulty = "Medium"
                            else:
                                difficulty = "Hard"
                            st.session_state.suggested_difficulty = difficulty
                        except (ValueError, IndexError):
                            st.session_state.suggested_difficulty = "Medium"
                            st.warning("Could not determine experience level precisely, defaulting to Medium difficulty.")

                        # Display analysis results
                        st.success("✅ CV Analysis Complete!")
                        st.markdown(f"""
                        ### Analysis Results
                        👤 **Candidate:** {analysis['candidate_name']}

                        📋 **Suggested Role:** {analysis['suggested_role']}

                        🔍 **Reasoning:** {analysis['reasoning']}

                        ⏳ **Experience:** {analysis['years_of_experience']}

                        💻 **Recommended Technologies:** {', '.join(analysis['recommended_languages'])}
                        """)

    # Only show the form after CV analysis
    if st.session_state.cv_uploaded:
        with st.form("candidate_profile_form"):
            with col2:
                st.markdown("### Start Your Assessment")
                role = st.selectbox(
                    "Expertise",
                    options=list(TECH_ROLES.keys()),
                    index=list(TECH_ROLES.keys()).index(st.session_state.suggested_role) if st.session_state.suggested_role else 0
                )

                if st.session_state.suggested_role and role != st.session_state.suggested_role:
                    st.info("Note: You've selected a different expertise than suggested based on your CV.")

            # Submit button inside the form
            submitted = st.form_submit_button("Start Technical Interview", use_container_width=True)

            if submitted and role:
                st.session_state.candidate_info = {
                    "name": st.session_state.candidate_name,
                    "role": role,
                    "id": st.session_state.candidate_id,
                    "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.profile_completed = True
                st.session_state.page = 'interview'
                st.rerun()
    else:
        st.info("👆 Please upload your CV to proceed with the assessment")

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

            difficulty = st.session_state.get('suggested_difficulty', role_info["difficulty"]) #Use suggested difficulty if available
            with col2:
                st.info(f"Difficulty Level: {difficulty}")

            if st.form_submit_button("Begin Interview"):
                with st.spinner("Generating questions..."):
                    questions = generate_questions(language, difficulty)
                    if questions:  # Only proceed if questions were generated successfully
                        st.session_state.questions = questions
                        st.session_state.start_time = time.time()
                        st.rerun()
                    else:
                        st.error("Failed to generate questions. Please try again.")
                        time.sleep(2)  # Give user time to read the error
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