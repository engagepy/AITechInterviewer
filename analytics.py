import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from openai import OpenAI
import os
import json
import base64
from datetime import datetime
import io
import pytz
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Initialize OpenAI client
openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Set timezone to US/New York
ny_timezone = pytz.timezone('America/New_York')

def fig_to_img(fig, width=500):
    """Convert plotly figure to reportlab Image"""
    # Convert to SVG and encode to base64
    svg_str = fig.to_image(format="svg")

    # Create a temporary file-like object to hold the SVG data
    img_buffer = io.BytesIO(svg_str)

    # Create and return the Image object
    return Image(img_buffer, width=width, height=width * 0.6)

def calculate_score(questions, answers):
    correct = 0
    for q, a in zip(questions, answers):
        if a == q["correct_answer"]:
            correct += 1
    return (correct / len(questions)) * 100

def analyze_notes(notes, role):
    if not any(notes) or all(note.strip() == "" for note in notes):
        return None

    prompt = f"""Analyze these interview notes for a {role} position and provide insights:
    {notes}
    Provide analysis in JSON format with fields:
    - key_observations: list of main points relevant to the role
    - strengths: list of technical and soft skills demonstrated
    - areas_of_improvement: list of potential areas to improve
    - role_fit: a score from 0-100 indicating fit for the role
    - recommendations: specific suggestions for improvement"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return None

def create_pdf_report(analytics_data, figures):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph("Technical Interview Assessment Report", title_style))
    story.append(Spacer(1, 20))

    # Candidate Information
    story.append(Paragraph("Candidate Information", styles['Heading2']))
    story.append(Paragraph(f"Name: {analytics_data['candidate_info']['name']}", styles['Normal']))
    story.append(Paragraph(f"ID: {analytics_data['candidate_info']['id']}", styles['Normal']))
    story.append(Paragraph(f"Role: {analytics_data['candidate_info']['role']}", styles['Normal']))

    # Convert timestamp to NY timezone
    date_obj = datetime.strptime(analytics_data['candidate_info']['datetime'], "%Y-%m-%d %H:%M:%S")
    ny_time = pytz.utc.localize(date_obj).astimezone(ny_timezone)
    story.append(Paragraph(f"Date: {ny_time.strftime('%Y-%m-%d %I:%M:%S %p %Z')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Performance Summary
    story.append(Paragraph("Performance Summary", styles['Heading2']))
    story.append(Paragraph(f"Overall Score: {analytics_data['score']:.1f}%", styles['Normal']))
    story.append(Paragraph(f"Average Time per Question: {analytics_data['avg_time']:.1f}s", styles['Normal']))
    story.append(Spacer(1, 20))

    # Analysis
    if analytics_data['notes_analysis']:
        story.append(Paragraph("Detailed Analysis", styles['Heading2']))
        story.append(Paragraph("Key Observations:", styles['Heading3']))
        for obs in analytics_data['notes_analysis']['key_observations']:
            story.append(Paragraph(f"• {obs}", styles['Normal']))

        story.append(Spacer(1, 10))
        story.append(Paragraph("Strengths:", styles['Heading3']))
        for strength in analytics_data['notes_analysis']['strengths']:
            story.append(Paragraph(f"✓ {strength}", styles['Normal']))

        story.append(Spacer(1, 10))
        story.append(Paragraph("Areas for Improvement:", styles['Heading3']))
        for area in analytics_data['notes_analysis']['areas_of_improvement']:
            story.append(Paragraph(f"△ {area}", styles['Normal']))

        story.append(Spacer(1, 10))
        story.append(Paragraph("Recommendations:", styles['Heading3']))
        for rec in analytics_data['notes_analysis']['recommendations']:
            story.append(Paragraph(f"• {rec}", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_analytics(questions, answers, times, notes, candidate_info):
    # Score calculation
    score = calculate_score(questions, answers)
    avg_time = sum(times)/len(times)

    # Store analytics data and figures
    analytics_data = {
        "candidate_info": candidate_info,
        "score": score,
        "avg_time": avg_time,
        "notes_analysis": analyze_notes(notes, candidate_info["role"])
    }

    figures = {}

    # Display performance overview
    st.header("📊 Performance Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Score", f"{score:.1f}%")
    with col2:
        st.metric("Avg. Time/Question", f"{avg_time:.1f}s")
    with col3:
        st.metric("Total Time", f"{sum(times):.1f}s")
    with col4:
        st.metric("Questions Completed", f"{len(answers)}/10")

    # Time analysis with improved visualization
    st.subheader("⏱️ Time Analysis")
    fig_time = go.Figure(data=[
        go.Bar(
            x=[f"Q{i+1}" for i in range(len(times))],
            y=times,
            marker_color='rgb(26, 115, 232)',
            marker_pattern_shape="/"
        )
    ])
    fig_time.update_layout(
        title="Time Spent per Question",
        xaxis_title="Question Number",
        yaxis_title="Time (seconds)",
        template="plotly_white"
    )
    st.plotly_chart(fig_time, use_container_width=True)
    figures["Time Analysis"] = fig_time

    # Question performance with enhanced visuals
    correct_answers = [
        1 if a == q["correct_answer"] else 0
        for q, a in zip(questions, answers)
    ]

    fig_performance = px.pie(
        values=[sum(correct_answers), len(questions) - sum(correct_answers)],
        names=['Correct', 'Incorrect'],
        title='Answer Distribution',
        color_discrete_sequence=['rgb(52, 168, 83)', 'rgb(234, 67, 53)']
    )
    fig_performance.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_performance, use_container_width=True)
    figures["Answer Distribution"] = fig_performance

    # Question-wise analysis with scatter plot
    df = pd.DataFrame({
        'Question': [f"Q{i+1}" for i in range(len(questions))],
        'Result': ['Correct' if c else 'Incorrect' for c in correct_answers],
        'Time': times
    })

    fig_scatter = px.scatter(
        df,
        x='Question',
        y='Time',
        color='Result',
        size=[30] * len(df),
        title='Performance vs Time Analysis',
        color_discrete_map={
            'Correct': 'rgb(52, 168, 83)',
            'Incorrect': 'rgb(234, 67, 53)'
        }
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    figures["Performance vs Time"] = fig_scatter

    # AI Analysis of notes
    if analytics_data['notes_analysis']:
        st.header("🤖 AI-Powered Insights")

        # Role fit gauge
        role_fit = analytics_data['notes_analysis'].get('role_fit', 0)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = role_fit,
            title = {'text': "Role Fit Score"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "rgb(26, 115, 232)"},
                'steps': [
                    {'range': [0, 40], 'color': "rgb(234, 67, 53)"},
                    {'range': [40, 70], 'color': "rgb(251, 188, 4)"},
                    {'range': [70, 100], 'color': "rgb(52, 168, 83)"}
                ]
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)
        figures["Role Fit Score"] = fig_gauge

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("💪 Strengths")
            for strength in analytics_data['notes_analysis']['strengths']:
                st.success(f"✓ {strength}")

        with col2:
            st.subheader("🎯 Areas for Improvement")
            for area in analytics_data['notes_analysis']['areas_of_improvement']:
                st.warning(f"△ {area}")

        st.subheader("📝 Key Observations")
        for obs in analytics_data['notes_analysis']['key_observations']:
            st.info(f"• {obs}")

        st.subheader("🚀 Recommendations")
        for rec in analytics_data['notes_analysis']['recommendations']:
            st.write(f"• {rec}")

    # Generate PDF report with charts
    pdf_buffer = create_pdf_report(analytics_data, figures)

    # Get the current time in NY timezone for the filename
    ny_now = datetime.now(ny_timezone)
    st.download_button(
        label="📥 Download Full Report (PDF)",
        data=pdf_buffer,
        file_name=f"interview_report_{candidate_info['id']}_{ny_now.strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )