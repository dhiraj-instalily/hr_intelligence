#!/usr/bin/env python3
"""
Script to extract individual resumes from a processed text file and structure them according to the schema.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.retrieval.schema import Resume, ContactInfo, Education, WorkExperience

logger = get_logger(__name__)

def extract_resumes(text_file_path: str, output_dir: str) -> List[Dict[str, Any]]:
    """
    Extract individual resumes from a processed text file.

    Args:
        text_file_path: Path to the processed text file
        output_dir: Directory to save individual resume JSON files

    Returns:
        List of extracted resume data dictionaries
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Read the processed text file
    with open(text_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split the content into individual resumes
    # Pattern: Look for a line that starts with a # followed by a name (no other # characters in the line)
    # This assumes each resume starts with the candidate's name as a heading
    resume_pattern = r'(?=# [A-Za-z]+ [A-Za-z]+\n(?:[^#]|#[^#])*)'
    resumes_text = re.split(resume_pattern, content)

    # Filter out the initial part (job description and applicant list)
    resumes_text = [text for text in resumes_text if re.search(r'# [A-Za-z]+ [A-Za-z]+\n', text)]

    logger.info(f"Found {len(resumes_text)} potential resumes in the text file")

    # Process each resume
    extracted_resumes = []

    for i, resume_text in enumerate(resumes_text):
        try:
            # Extract candidate name
            name_match = re.search(r'# ([A-Za-z]+ [A-Za-z]+)', resume_text)
            if not name_match:
                logger.warning(f"Could not extract name from resume {i+1}, skipping")
                continue

            candidate_name = name_match.group(1)
            logger.info(f"Processing resume for {candidate_name}")

            # Extract contact information
            email = extract_email(resume_text)
            phone = extract_phone(resume_text)
            linkedin = extract_linkedin(resume_text)

            # Extract education
            education_list = extract_education(resume_text)

            # Extract work experience
            work_experience_list = extract_work_experience(resume_text)

            # Extract skills
            skills = extract_skills(resume_text)

            # Extract certifications
            certifications = extract_certifications(resume_text)

            # Extract summary/profile
            summary = extract_summary(resume_text)

            # Create resume dictionary
            resume_data = {
                "document_type": "resume",
                "candidate_name": candidate_name,
                "contact_info": {
                    "email": email,
                    "phone": phone,
                    "linkedin": linkedin,
                    "address": None,
                    "website": None
                },
                "education": education_list,
                "work_experience": work_experience_list,
                "skills": skills,
                "certifications": certifications,
                "summary": summary
            }

            # Validate against schema
            try:
                Resume(**resume_data)
                logger.info(f"Resume for {candidate_name} validated successfully")
            except Exception as e:
                logger.warning(f"Resume for {candidate_name} failed validation: {e}")
                # Continue processing even if validation fails

            # Save to JSON file
            output_file = output_path / f"{candidate_name.replace(' ', '_')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(resume_data, f, indent=2)

            logger.info(f"Saved resume for {candidate_name} to {output_file}")
            extracted_resumes.append(resume_data)

        except Exception as e:
            logger.error(f"Error processing resume {i+1}: {e}")

    logger.info(f"Successfully extracted {len(extracted_resumes)} resumes")
    return extracted_resumes

def extract_email(text: str) -> str:
    """Extract email address from text."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""

def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text."""
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
        r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # +1 (123) 456-7890
    ]

    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    return None

def extract_linkedin(text: str) -> Optional[str]:
    """Extract LinkedIn URL or username from text."""
    linkedin_patterns = [
        r'linkedin\.com/in/[A-Za-z0-9_-]+',
        r'linkedin\.com/[A-Za-z0-9_-]+',
        r'linkedin: [A-Za-z0-9_-]+'
    ]

    for pattern in linkedin_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    return None

def extract_education(text: str) -> List[Dict[str, Any]]:
    """Extract education information from text."""
    education_list = []

    # Look for education section
    education_section_match = re.search(r'# Education:?(.*?)(?=# [A-Za-z]+:|$)', text, re.DOTALL)
    if not education_section_match:
        education_section_match = re.search(r'# EDUCATION:?(.*?)(?=# [A-Za-z]+:|$)', text, re.DOTALL)

    if education_section_match:
        education_text = education_section_match.group(1)

        # Look for institutions
        institutions = re.findall(r'([A-Za-z]+ [A-Za-z]+ [A-Za-z]+|[A-Za-z]+ [A-Za-z]+|[A-Za-z]+)[,\n].*?(?:University|College|School)', education_text)

        for institution in institutions:
            # Extract degree
            degree_match = re.search(r'(Bachelor|Master|B\.S\.|M\.S\.|B\.A\.|M\.A\.|PhD|Ph\.D\.|BSc|MSc|MBA)\.? (?:of|in)? ([A-Za-z]+(?: [A-Za-z]+)*)', education_text)
            degree = degree_match.group(0) if degree_match else "Degree not specified"

            # Extract dates
            dates_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4} [-–] (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|(\d{4} [-–] \d{4})|(\d{4} [-–] Present)|(\d{4} [-–] \d{2})|(\d{4})', education_text)
            dates = dates_match.group(0) if dates_match else ""

            # Extract GPA
            gpa_match = re.search(r'GPA:? (\d+\.\d+)', education_text)
            gpa = float(gpa_match.group(1)) if gpa_match else None

            education_list.append({
                "institution": institution.strip(),
                "degree": degree,
                "dates": dates,
                "graduation_date": None,  # Would need more complex parsing
                "gpa": gpa
            })

    return education_list

def extract_work_experience(text: str) -> List[Dict[str, Any]]:
    """Extract work experience information from text."""
    work_experience_list = []

    # Look for experience section
    experience_section_match = re.search(r'# (Experience|EXPERIENCE|Work Experience|WORK EXPERIENCE):?(.*?)(?=# [A-Za-z]+:|$)', text, re.DOTALL)

    if experience_section_match:
        experience_text = experience_section_match.group(2)

        # Split into individual experiences
        experiences = re.split(r'# [A-Za-z]', experience_text)

        for exp in experiences:
            if not exp.strip():
                continue

            # Extract company
            company_match = re.search(r'([A-Za-z]+ [A-Za-z]+ [A-Za-z]+|[A-Za-z]+ [A-Za-z]+|[A-Za-z]+)[,\n]', exp)
            company = company_match.group(1) if company_match else "Company not specified"

            # Extract role
            role_match = re.search(r'(Engineer|Developer|Analyst|Manager|Intern|Assistant|Specialist|Lead|Director|Consultant)(?:[,\n]|$)', exp)
            role = role_match.group(1) if role_match else "Role not specified"

            # Extract dates
            dates_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4} [-–] (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|(\d{4} [-–] \d{4})|(\d{4} [-–] Present)|(\d{4} [-–] \d{2})|(\d{2}/\d{4} [-–] \d{2}/\d{4})|(\d{2}/\d{4} [-–] Present)', exp)
            dates = dates_match.group(0) if dates_match else ""

            # Extract responsibilities
            responsibilities = []
            bullet_points = re.findall(r'- (.*?)(?=\n- |\n\n|$)', exp)
            for point in bullet_points:
                if point.strip():
                    responsibilities.append(point.strip())

            work_experience_list.append({
                "company": company.strip(),
                "role": role,
                "dates": dates,
                "start_date": None,  # Would need more complex parsing
                "end_date": None,  # Would need more complex parsing
                "responsibilities": responsibilities
            })

    return work_experience_list

def extract_skills(text: str) -> List[str]:
    """Extract skills from text."""
    skills = []

    # Look for skills section
    skills_section_match = re.search(r'# (Skills|SKILLS|Technical Skills|TECHNICAL SKILLS):?(.*?)(?=# [A-Za-z]+:|$)', text, re.DOTALL)

    if skills_section_match:
        skills_text = skills_section_match.group(2)

        # Extract skills from bullet points
        bullet_skills = re.findall(r'- (.*?)(?=\n- |\n\n|$)', skills_text)
        for skill in bullet_skills:
            if skill.strip():
                skills.append(skill.strip())

        # Extract skills from comma-separated lists
        if not skills:
            skill_lists = re.findall(r'([A-Za-z]+(?:[,/&]? [A-Za-z]+)*(?:, [A-Za-z]+(?:[,/&]? [A-Za-z]+)*)+)', skills_text)
            for skill_list in skill_lists:
                for skill in skill_list.split(', '):
                    if skill.strip():
                        skills.append(skill.strip())

    return skills

def extract_certifications(text: str) -> Optional[List[str]]:
    """Extract certifications from text."""
    certifications = []

    # Look for certifications section
    cert_section_match = re.search(r'# (Certifications|CERTIFICATIONS):?(.*?)(?=# [A-Za-z]+:|$)', text, re.DOTALL)

    if cert_section_match:
        cert_text = cert_section_match.group(2)

        # Extract certifications from bullet points
        bullet_certs = re.findall(r'- (.*?)(?=\n- |\n\n|$)', cert_text)
        for cert in bullet_certs:
            if cert.strip():
                certifications.append(cert.strip())

    return certifications if certifications else None

def extract_summary(text: str) -> Optional[str]:
    """Extract summary/profile from text."""
    # Look for summary/profile section
    summary_section_match = re.search(r'# (Profile|PROFILE|Summary|SUMMARY|Professional Summary):?(.*?)(?=# [A-Za-z]+:|$)', text, re.DOTALL)

    if summary_section_match:
        summary_text = summary_section_match.group(2).strip()
        return summary_text

    return None

def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract individual resumes from a processed text file")

    parser.add_argument(
        "--input-file",
        type=str,
        default="data/processed_text/Sales Engineer AI Growth.txt",
        help="Path to the processed text file"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/extracted_resumes",
        help="Directory to save individual resume JSON files"
    )

    args = parser.parse_args()

    # Extract resumes
    extracted_resumes = extract_resumes(args.input_file, args.output_dir)

    print(f"Successfully extracted {len(extracted_resumes)} resumes to {args.output_dir}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
