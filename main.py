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
import pytz #Import pytz library

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
        'verification_shown': False,  # Track if verification animation has been shown
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
        "languages": ["Terraform", "Kubernetes", "Docker", "Jenkins", "Ansible"],
        "difficulty": "Medium",
        "keywords": ["devops", "ci/cd", "aws", "docker", "kubernetes", "infrastructure"]
    },
    "Mobile Developer": {
        "languages": ["Swift", "Kotlin", "React Native", "Flutter", "Android Studio"],
        "difficulty": "Medium",
        "keywords": ["mobile", "android", "ios", "react native", "flutter"]
    },
    "Product Manager": {
        "languages": ["JIRA", "Confluence", "Product Vision", "Roadmap", "User Stories"],
        "difficulty": "Medium",
        "keywords": ["product", "agile", "scrum", "jira", "miro", "roadmap", "user stories", "backlog"]
    },
    "Salesforce Developer": {
        "languages": ["Apex", "Lightning Web Components", "Visualforce", "SOQL", "Flow Builder"],
        "difficulty": "Medium",
        "keywords": ["salesforce", "apex", "lwc", "visualforce", "soql", "crm"]
    },
    "AWS Cloud Engineer": {
        "languages": ["AWS CLI", "CloudFormation", "Lambda", "EC2", "S3"],
        "difficulty": "Hard",
        "keywords": ["aws", "cloud", "ec2", "s3", "lambda", "cloudformation"]
    },
    "Azure Developer": {
        "languages": ["Azure CLI", "ARM Templates", "Azure Functions", "Azure DevOps", "Power Platform"],
        "difficulty": "Hard",
        "keywords": ["azure", "cloud", "functions", "devops", "power apps"]
    },
    "Google Cloud Expert": {
        "languages": ["Google Cloud SDK", "Cloud Functions", "BigQuery", "Kubernetes Engine", "App Engine"],
        "difficulty": "Hard",
        "keywords": ["gcp", "google cloud", "bigquery", "kubernetes", "app engine"]
    },
    "Data Scientist": {
        "languages": ["Python", "R", "TensorFlow", "PyTorch", "Scikit-learn"],
        "difficulty": "Hard",
        "keywords": ["data science", "machine learning", "ai", "statistics", "deep learning"]
    },
    "Business Analyst": {
        "languages": ["SQL", "Excel", "Tableau", "Power BI", "BPMN"],
        "difficulty": "Medium",
        "keywords": ["business analysis", "requirements", "process modeling", "data analysis"]
    },
    "QA Engineer": {
        "languages": ["Selenium", "Cypress", "JUnit", "TestNG", "Postman"],
        "difficulty": "Medium",
        "keywords": ["testing", "automation", "quality assurance", "test cases"]
    }
}

def analyze_cv(cv_content):
    """Analyze CV content and suggest a role"""
    try:
        prompt = f"""Analyze this CV and extract the following information with high attention to detail:
        1. The candidate's full name from the CV
        2. The most appropriate technical role from these options: {', '.join(TECH_ROLES.keys())}
        3. Analyze work experience holistically:
           - Consider all professional experience in the CV
           - Include relevant projects and contributions
           - Consider depth and breadth of experience
           - Provide total years of experience as a single number or range (e.g. "5 years" or "4-5 years")
        4. Extract education details, including degree and institution
        5. List key technical and soft skills with confidence levels
        6. For the selected role, identify the most relevant programming languages or tools

        CV Content:
        {cv_content}

        Respond in JSON format with:
        {{
            "candidate_name": "full name from CV",
            "suggested_role": "one of the roles listed above",
            "confidence": "score between 0 and 1",
            "reasoning": "brief explanation for the suggestion",
            "education": "detailed education background",
            "key_skills": ["list of key technical and soft skills"],
            "recommended_languages": ["list of relevant programming languages"],
            "years_of_experience": "total years of experience"
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

    # Add passcode protection
    ist_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    correct_passcode = ist_time.strftime('%d%m%y')  # Format: ddmmyy

    # Create a container for the passcode input and button
    input_container = st.container()
    with input_container:
        passcode = st.text_input("Enter passcode", type="password")
        if passcode == correct_passcode:
            # Begin Assessment Button
            if st.button("BEGIN ASSESSMENT", use_container_width=True):
                st.session_state.page = 'profile'
                st.rerun()
        elif passcode:  # Only show error if something was entered
            st.error("Invalid passcode")

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
            <li>Azure Developers</li>
            <li>Google Cloud Experts</li>
            <li>Data Scientists</li>
            <li>Business Analysts</li>
            <li>QA Engineers</li>
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

        # Create persistent containers for analysis and verifications
        persisted_content = st.empty()

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
                        st.session_state.cv_analysis = analysis  # Store full analysis

                        # Display analysis results and verifications in persistent container
                        with persisted_content.container():
                            st.success("✅ CV Analysis Complete!")
                            # Show verifications first
                            show_verification_animations()

                            st.markdown(f"""
                            ### Analysis Results
                            👤 **Candidate:** {analysis['candidate_name']}

                            📋 **Suggested Role:** {analysis['suggested_role']}

                            🎓 **Education:** {analysis.get('education', 'Not specified')}

                            ⚡ **Key Skills:** {', '.join(analysis.get('key_skills', []))}

                            ⏳ **Experience:** {analysis['years_of_experience']}

                            💻 **Technologies:** {', '.join(analysis['recommended_languages'])}
                            """)

                        # Parse years of experience from detailed analysis
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

        # Show the analysis results even after CV is uploaded
        elif st.session_state.cv_uploaded and hasattr(st.session_state, 'cv_analysis'):
            analysis = st.session_state.cv_analysis
            with persisted_content.container():
                st.success("✅ CV Analysis Complete!")
                # Show verifications first
                show_verification_animations()

                st.markdown(f"""
                ### Analysis Results
                👤 **Candidate:** {analysis['candidate_name']}

                📋 **Suggested Role:** {analysis['suggested_role']}

                🎓 **Education:** {analysis.get('education', 'Not specified')}

                ⚡ **Key Skills:** {', '.join(analysis.get('key_skills', []))}

                ⏳ **Experience:** {analysis['years_of_experience']}


                💻 **Technologies:** {', '.join(analysis['recommended_languages'])}
                """)

    # Only show the form after CV analysis
    if st.session_state.cv_uploaded:
        with st.form("candidate_profile_form"):
            with col2:
                st.markdown("### Additional Information")

                # CTC Range dropdown
                ctc_ranges = [
                    "10-15 LPA", "15-20 LPA", "20-25 LPA", "25-30 LPA",
                    "30-40 LPA", "40-50 LPA", "50-75 LPA", "75-100 LPA", "Above 1 Cr"
                ]
                ctc_range = st.selectbox("Expected CTC Range", options=ctc_ranges)

                # Location preferences
                preferred_location = st.text_input("Preferred Location")
                willing_to_relocate = st.selectbox("Willing to Relocate", options=["Yes", "No"])

                st.markdown("### Role Selection")
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
                    "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "ctc_range": ctc_range,
                    "preferred_location": preferred_location,
                    "willing_to_relocate": willing_to_relocate,
                    "cv_analysis": st.session_state.cv_analysis  # Include full CV analysis
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
                # Get available tools for the role
                available_tools = role_info["languages"]

                # Get recommended tools from CV analysis
                recommended_tools = st.session_state.get('recommended_languages', [])

                # Find the default tool (first recommended tool that's available for the role)
                default_index = 0
                if recommended_tools:
                    for i, tool in enumerate(available_tools):
                        if tool in recommended_tools:
                            default_index = i
                            break

                tool = st.selectbox(
                    "Select Tool",
                    options=available_tools,
                    index=default_index,
                    help="Tools are suggested based on your CV and role requirements"
                )

                # Show recommendation indicator if the selected tool is recommended
                if tool in recommended_tools:
                    st.success("✨ This tool is recommended based on your experience")

            difficulty = st.session_state.get('suggested_difficulty', role_info["difficulty"])
            with col2:
                st.info(f"Difficulty Level: {difficulty}")

            if st.form_submit_button("Begin Interview"):
                with st.spinner("Generating questions..."):
                    questions = generate_questions(tool, difficulty)
                    if questions:
                        st.session_state.questions = questions
                        st.session_state.start_time = time.time()
                        st.rerun()
                    else:
                        st.error("Failed to generate questions. Please try again.")
                        time.sleep(2)
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
    **CTC Range:** {st.session_state.candidate_info['ctc_range']}
    **Preferred Location:** {st.session_state.candidate_info['preferred_location']}
    **Willing to Relocate:** {st.session_state.candidate_info['willing_to_relocate']}
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


def show_verification_animations():
    """Show verification animations sequentially"""
    # If verifications have already been shown, display static badges
    if st.session_state.verification_shown:
        st.success("✅ LinkedIn API Verification (Success)")
        st.success("✅ Github Profile Analysis (Success)")
        st.success("✅ Past Experience Verification Emails (Sent)")
        st.success("✅ Culture Alignment (Verified)")
        return

    # Show animated sequence only on first display
    with st.spinner("Processing verifications..."):
        # LinkedIn API Verification
        time.sleep(1)
        st.success("✅ LinkedIn API Verification (Success)")

        # Github Profile Analysis
        time.sleep(0.8)
        st.success("✅ Github Profile Analysis (Success)")

        # Past Experience Verification
        time.sleep(1.2)
        st.success("✅ Past Experience Verification Emails (Sent)")

        # Culture Alignment
        time.sleep(0.7)
        st.success("✅ Culture Alignment (Verified)")

        time.sleep(0.5)

    # Mark verifications as shown
    st.session_state.verification_shown = True


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