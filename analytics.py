import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from openai import OpenAI
import os

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def calculate_score(questions, answers):
    correct = 0
    for q, a in zip(questions, answers):
        if a == q["correct_answer"]:
            correct += 1
    return (correct / len(questions)) * 100

def analyze_notes(notes):
    if not any(notes) or all(note.strip() == "" for note in notes):
        return None
    
    prompt = f"""Analyze these interview notes and provide insights about the candidate's thought process:
    {notes}
    Provide analysis in JSON format with fields:
    - key_observations: list of main points
    - strengths: list of apparent strengths
    - areas_of_improvement: list of potential areas to improve"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return None

def generate_analytics(questions, answers, times, notes):
    # Score calculation
    score = calculate_score(questions, answers)
    
    # Display score
    st.header("Interview Results")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Score", f"{score:.1f}%")
    with col2:
        st.metric("Average Time per Question", f"{(sum(times)/len(times)):.1f}s")
    with col3:
        st.metric("Total Time", f"{sum(times):.1f}s")
    
    # Time analysis
    fig_time = go.Figure(data=[
        go.Bar(
            x=[f"Q{i+1}" for i in range(len(times))],
            y=times,
            marker_color='lightblue'
        )
    ])
    fig_time.update_layout(
        title="Time Spent per Question",
        xaxis_title="Question Number",
        yaxis_title="Time (seconds)"
    )
    st.plotly_chart(fig_time)
    
    # Question performance
    correct_answers = [
        1 if a == q["correct_answer"] else 0
        for q, a in zip(questions, answers)
    ]
    
    fig_performance = px.pie(
        values=[sum(correct_answers), len(questions) - sum(correct_answers)],
        names=['Correct', 'Incorrect'],
        title='Answer Distribution'
    )
    st.plotly_chart(fig_performance)
    
    # Question-wise analysis
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
        title='Performance vs Time Analysis'
    )
    st.plotly_chart(fig_scatter)
    
    # Notes analysis
    notes_analysis = analyze_notes(notes)
    if notes_analysis:
        st.header("Notes Analysis")
        
        with st.expander("Key Observations"):
            for obs in notes_analysis["key_observations"]:
                st.write(f"• {obs}")
                
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Strengths")
            for strength in notes_analysis["strengths"]:
                st.write(f"✓ {strength}")
        
        with col2:
            st.subheader("Areas for Improvement")
            for area in notes_analysis["areas_of_improvement"]:
                st.write(f"△ {area}")
