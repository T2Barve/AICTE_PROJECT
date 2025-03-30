import os
import json
import google.generativeai as genai
import PyPDF2 as pdf
import streamlit as st
import pandas as pd

# Configure API Key
genai.configure(api_key="AIzaSyCsObYuzbzMTAf2MmME4n8xNRwvoOJrbNw")


# Function to get AI response
def get_response(resumes, jd):
    model = genai.GenerativeModel('gemini-1.5-pro')

    input_prompt = f"""
    You are an AI-powered Applicant Tracking System (ATS) designed to analyze resumes based on a given job description.

    - Extract: Candidate Name, Experience, Skills, Education, Certifications.
    - Compare with job description and calculate Match Percentage.
    - Assign ATS Score (0-100) based on relevance.
    - List missing keywords.
    - Provide a brief Profile Summary.
    - Rank candidates from highest to lowest.

    Return **ONLY JSON** in the following format:
    ```json
    [
        {{
            "Candidate Name": "John Doe",
            "ATS Score": 95,
            "Match Percentage": "95%",
            "Missing Keywords": [],
            "Rank": 1,
            "Profile Summary": "Experienced Software Engineer...",
            "Experience": "5+ years",
            "Skills": ["Python", "Django", "React.js"],
            "Education": "B.Tech in Computer Science",
            "Certifications": ["AWS Certified Developer"]
        }}
    ]
    ```

    Job Description: {jd}

    Resume Data: {resumes}
    """

    response = model.generate_content(input_prompt)
    return response.text


# Function to extract text from PDFs
def extract_text_from_pdf(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = "".join([page.extract_text() or "" for page in reader.pages])
    return {"filename": uploaded_file.name, "text": text}


# Streamlit UI Configuration
st.set_page_config(page_title="Smart ATS", layout="wide")
st.title("📄 Smart Applicant Tracking System")

st.divider()
st.subheader("📋 Job Description Input")
jd = st.text_area("Paste the job description here:", height=200, placeholder="Enter job description...")

st.divider()
st.subheader("📤 Resume Input Options")

col1, col2 = st.columns(2)
with col1:
    uploaded_files = st.file_uploader("Upload PDF Resumes", type="pdf", accept_multiple_files=True)
with col2:
    text_resume = st.text_area("Or paste resume text here:", height=200, placeholder="Paste resume text...")

st.divider()
if st.button("🚀 Analyze Resumes", use_container_width=True):
    if not jd:
        st.warning("⚠ Please enter a job description first")
        st.stop()

    resumes = []

    # Process uploaded PDFs
    if uploaded_files:
        for file in uploaded_files:
            pdf_data = extract_text_from_pdf(file)
            resumes.append(pdf_data)

    # Process text resume
    if text_resume.strip():
        resumes.append({"filename": "Text Resume", "text": text_resume})

    if not resumes:
        st.warning("⚠ Please upload resumes or paste text resume")
        st.stop()

    try:
        with st.spinner("🔍 Analyzing resumes..."):
            result = get_response(resumes, jd)

            # Ensure AI response is valid JSON
            cleaned_result = result.strip()

            # Force valid JSON by checking first & last characters
            if not (cleaned_result.startswith("[") and cleaned_result.endswith("]")):
                raise ValueError("Invalid AI response format")

            ats_data = json.loads(cleaned_result)

            # Display results
            st.divider()
            st.subheader("📊 Analysis Results")

            for candidate in sorted(ats_data, key=lambda x: x['Rank']):
                with st.expander(
                        f"🏆 #{candidate['Rank']} | {candidate['Candidate Name']} | Score: {candidate['ATS Score']}/100"):
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.metric("Match Percentage", candidate['Match Percentage'])
                        st.write(f"Missing Keywords:\n{', '.join(candidate['Missing Keywords']) or 'None'}")
                    with cols[1]:
                        st.write("Profile Summary:")
                        st.write(candidate['Profile Summary'])

            st.download_button("📥 Download Full Report",
                               data=json.dumps(ats_data, indent=2),
                               file_name="ats_analysis.json",
                               mime="application/json")

    except json.JSONDecodeError:
        st.error("❌ AI Response Error: Invalid JSON format from AI.")
        st.text("Raw API Response:")
        st.code(result)

    except Exception as e:
        st.error(f"❌ AI Response Error: {str(e)}")
        st.text("Raw API Response:")
        st.code(result)
