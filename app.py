from flask import Flask, render_template, request
import pandas as pd
import re
from PyPDF2 import PdfReader
import docx

app = Flask(__name__)

# Load job dataset
data_path = "updated_job_skills_dataset.csv"
jobs_df = pd.read_csv(data_path)

# Utility functions
def extract_skills(resume_text):
    """
    Extract skills from the resume text using a predefined skill list.
    Ensure extracted skills are returned in the original format from the dataset.
    """
    predefined_skills = {
        skill.strip(): skill.strip()  # Create a mapping of original skill to itself
        for skills in jobs_df["Required Skills"]
        for skill in skills.split(",")
    }
    extracted_skills = [
        predefined_skills[skill]  # Return the skill in its original format
        for skill in predefined_skills
        if re.search(skill, resume_text, re.IGNORECASE)
    ]
    return [skill for skill in extracted_skills]  # Convert all to uppercase


def match_jobs(extracted_skills):
    """
    Match extracted skills with jobs in the dataset.
    Return the jobs sorted by the number of matching skills.
    Ensure matching considers the exact format from the dataset.
    """
    extracted_skills_set = set(extracted_skills)  # Convert extracted skills to a set for quick lookups
    job_matches = []

    for _, row in jobs_df.iterrows():
        required_skills = {skill.strip() for skill in row["Required Skills"].split(",")}
        matching_skills = required_skills.intersection(extracted_skills_set)
        if matching_skills:
            job_matches.append({
                "Job Title": row["Job Title"],
                "Matching Skills": list(matching_skills),
                "Match Count": len(matching_skills)
            })

    # Sort the job matches by the number of matching skills (descending)
    return sorted(job_matches, key=lambda x: x["Match Count"], reverse=True)

def read_file_content(file):
    """
    Reads the content of the uploaded file. Supports TXT, PDF, and DOCX formats.
    """
    filename = file.filename.lower()
    if filename.endswith('.txt'):
        return file.read().decode('utf-8')
    elif filename.endswith('.pdf'):
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    elif filename.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file format. Please upload a TXT, PDF, or DOCX file.")

# Flask routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        return "Error: Please upload a resume."

    # Read uploaded resume
    resume_file = request.files['resume']
    try:
        resume_text = read_file_content(resume_file)
    except Exception as e:
        return f"Error processing file: {str(e)}"

    # Extract skills and match jobs
    extracted_skills = extract_skills(resume_text)
    job_matches = match_jobs(extracted_skills)

    return render_template('result.html', job_matches=job_matches, skills=extracted_skills)

if __name__ == '__main__':
    app.run(debug=True)
