import sys
import os

# Ensure the project root is in the system path
sys.path.append('C:/Users/HP/Downloads/Auto_job_applier_linkedIn-main/Auto_job_applier_linkedIn-main')

# Import AI-related functions
from ai_test import ai_extract_skills
from modules.ai.openaiConnections import ai_create_openai_client

# Import user details and settings
from config.personals import first_name, middle_name, last_name, email, phone_number, street, current_city, state, zipcode, country
from config.settings import generated_resume_path


def extract_job_info(job_description: str, client) -> dict:
    """
    Extracts relevant skills and job details from the given job description using AI.

    :param job_description: The job description text.
    :param client: The OpenAI client instance.
    :return: A dictionary containing extracted skills and job details.
    """
    skills = ai_extract_skills(client, job_description)  # Extract skills using AI
    return {
        "job_description": job_description,
        "skills": skills
    }


def create_resume(user_details, summary, experience, projects, skills, certificates, output_folder):
    """
    Generates a resume document based on provided user details and job-related skills.

    :param user_details: Dictionary containing user details.
    :param summary: Summary section for the resume.
    :param experience: Work experience list.
    :param projects: List of projects.
    :param skills: Extracted job-related skills.
    :param certificates: List of certifications.
    :param output_folder: Destination folder for the generated resume.
    """
    from modules.resumes.generator import create_resume_docx  # Import inside function to avoid circular dependency

    create_resume_docx(user_details, summary, experience, projects, skills, certificates, output_folder)


if __name__ == "__main__":
    # Initialize OpenAI client
    client = ai_create_openai_client()

    # Sample job description (this would typically be fetched dynamically)
    job_description = """
    We are looking for a Software Engineer with experience in Python, Java, and cloud technologies.
    The ideal candidate should have strong skills in backend development and be familiar with CI/CD pipelines.
    """

    # Extract job info using AI
    job_info = extract_job_info(job_description, client)

    # Prepare user details
    user_details = {
        'name': f"{first_name} {middle_name} {last_name}",
        'email': email,
        'phone_number': phone_number,
        'address': f"{street}, {current_city}, {state}, {zipcode}, {country}"
    }

    # Ensure the output folder exists
    os.makedirs(generated_resume_path, exist_ok=True)

    # Generate resume
    create_resume(user_details, "A motivated software engineer.", [], [], job_info['skills'], [], generated_resume_path)

    print("✅ Resume has been successfully created!")
