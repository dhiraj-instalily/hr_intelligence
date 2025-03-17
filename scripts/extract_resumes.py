#!/usr/bin/env python3
"""
Script to extract individual resumes from a processed text file and structure them according to the schema.

Improvements:
- Added support for cleaning the output directory before extraction (--clean flag)
- Fixed extraction of non-candidate headings (like "COMMUNITY_INVOLVEMENT", "PROFESSIONAL_EXPERIENCE")
- Added support for candidates with name variations (e.g., "Nimeesh Bagwe" vs "NIMEESH NILESH BAGWE")
- Implemented special case handling for hard-to-find candidates
- Added email-based search for candidates whose names can't be found in headings
- Improved heading pattern matching to handle different formatting styles
- FIXED: Improved resume extraction to capture the full text between candidate headings
- FIXED: Added debug output to verify extraction quality
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import shutil

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.retrieval.schema import Resume, ContactInfo, Education, WorkExperience

logger = get_logger(__name__)

def extract_candidate_names_from_table(text: str) -> List[Tuple[str, str]]:
    """
    Extract candidate names and emails from the tables at the beginning of the document.

    Args:
        text: The full text content of the document

    Returns:
        List of tuples containing (candidate_name, email)
    """
    # Find tables with candidate information
    table_pattern = r'\|Name\|Email Address\|.*?\|(.*?)(?=\n\n# )'
    tables = re.findall(table_pattern, text, re.DOTALL)

    candidates = []

    for table in tables:
        # Extract rows from the table
        rows = table.strip().split('\n')
        for row in rows:
            # Skip separator rows and empty rows
            if '---' in row or not row.strip():
                continue

            # Extract name and email from the row
            parts = row.split('|')
            if len(parts) >= 3:  # Ensure we have at least name and email
                name = parts[1].strip()
                email = parts[2].strip()
                if name and email and '@' in email:
                    candidates.append((name, email))

    logger.info(f"Extracted {len(candidates)} candidate names from tables")
    return candidates

def extract_resumes(text_file_path: str, output_dir: str, debug: bool = False) -> List[Dict[str, Any]]:
    """
    Extract individual resumes from a processed text file.

    Args:
        text_file_path: Path to the processed text file
        output_dir: Directory to save individual resume JSON files
        debug: Whether to print debug information

    Returns:
        List of extracted resume data dictionaries
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Read the processed text file
    with open(text_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract candidate names and emails from the tables at the beginning
    candidates = extract_candidate_names_from_table(content)

    if not candidates:
        logger.warning("No candidates found in the tables. Falling back to regex pattern matching.")
        # This fallback is now more restrictive to avoid matching section headers
        # It requires names to be in the format "Firstname Lastname" with proper capitalization
        name_pattern = r'# ([A-Z][a-z]+ [A-Z][a-z]+)\n'
        names = re.findall(name_pattern, content)

        # Additional filtering to exclude common section headers
        section_headers = ["PROFESSIONAL EXPERIENCE", "WORK EXPERIENCE", "EDUCATION", "SKILLS",
                          "CERTIFICATIONS", "COMMUNITY INVOLVEMENT", "EXTRACURRICULAR ACTIVITIES",
                          "SPECIALIZED SKILLS", "KEY SKILLS", "SPECIAL MENTIONS", "PROJECT EXPERIENCE",
                          "LEADERSHIP EXPERIENCE", "TECHNICAL SKILLS", "PROFESSIONAL SUMMARY"]

        candidates = [(name, "") for name in names if name not in section_headers]

        # Log the candidates found through regex
        logger.info(f"Found {len(candidates)} candidates through regex pattern matching")

    # Create a map to store resume content for each candidate
    resume_map = {}

    # Create a mapping of possible name variations
    name_variations = {
        "Nimeesh Bagwe": ["NIMEESH NILESH BAGWE", "NIMEESH BAGWE"],
        "Yoon Cho": ["SUNGYOON CHO", "Sungyoon Cho"],
        "Shubham Garg": ["SHUBHAM GARG"],
        "Varshitha Reddy Medarametla": ["VARSHITHA MEDARAMETLA"],
        "Aidan O'Donnell": ["AIDAN O'DONNELL", "AIDAN ODONNELL", "Aidan ODonnell", "Aidan O Donnell"],
        "Sai Sandeep Sandeep": ["SAI SANDEEP", "Sai Sandeep", "SAI SANDEEP SANDEEP"],
        "Cherry Tao": ["CHERRY TAO", "Cherry Y. Tao", "CHERRY Y TAO", "Cherry", "Tao"]
    }

    # Create a list of all candidate names and their variations for better matching
    all_candidate_variations = []
    for candidate_name, _ in candidates:
        all_candidate_variations.append(candidate_name)
        if candidate_name in name_variations:
            all_candidate_variations.extend(name_variations[candidate_name])

    # Find all headings in the document
    heading_matches = list(re.finditer(r'# ([^\n]+)', content))

    # Extract resume sections based on headings
    for i, (candidate_name, email) in enumerate(candidates):
        # Try to find the resume with the exact name or variations
        resume_found = False

        # List of possible name variations to try
        names_to_try = [candidate_name]

        # Add variations if they exist
        if candidate_name in name_variations:
            names_to_try.extend(name_variations[candidate_name])

        # Try each name variation
        for name_variation in names_to_try:
            # Find the heading that matches this candidate
            candidate_heading_index = None
            for j, match in enumerate(heading_matches):
                heading_text = match.group(1)
                # Check if the heading contains the candidate name (case insensitive)
                if name_variation.lower() in heading_text.lower():
                    candidate_heading_index = j
                    break

            if candidate_heading_index is not None:
                # Found the candidate's heading
                start_pos = heading_matches[candidate_heading_index].start()

                # Find the next candidate heading
                next_candidate_index = None
                for j in range(candidate_heading_index + 1, len(heading_matches)):
                    heading_text = heading_matches[j].group(1)
                    # Check if this heading is for another candidate
                    is_candidate_heading = False
                    for other_name in all_candidate_variations:
                        if other_name.lower() in heading_text.lower():
                            is_candidate_heading = True
                            break

                    # Skip headings that are clearly section headers
                    if heading_text in ["EDUCATION", "EXPERIENCE", "SKILLS", "PROJECTS", "WORK EXPERIENCE",
                                       "TECHNICAL SKILLS", "PROFESSIONAL EXPERIENCE"]:
                        continue

                    if is_candidate_heading:
                        next_candidate_index = j
                        break

                # If we found the next candidate, use their heading as the end point
                if next_candidate_index is not None:
                    end_pos = heading_matches[next_candidate_index].start()
                else:
                    # If this is the last candidate, go to the end of the document
                    end_pos = len(content)

                # Extract the resume content
                resume_text = content[start_pos:end_pos].strip()

                # Store in the map
                resume_map[candidate_name] = {
                    "text": resume_text,
                    "email": email
                }

                resume_found = True
                break

        # Special case for candidates we couldn't find
        if not resume_found:
            # Try to find by email
            if email:
                email_pattern = re.escape(email)
                email_match = re.search(email_pattern, content)

                if email_match:
                    # Find the nearest heading before this email
                    heading_pos = content[:email_match.start()].rfind("# ")
                    if heading_pos != -1:
                        start_pos = heading_pos

                        # Find the next candidate heading after this position
                        end_pos = len(content)
                        for other_name, _ in candidates:
                            if other_name != candidate_name:
                                other_pattern = f"# {re.escape(other_name)}"
                                other_match = re.search(other_pattern, content[email_match.end():])
                                if other_match:
                                    end_pos = email_match.end() + other_match.start()
                                    break

                            # Extract the resume content
                            resume_text = content[start_pos:end_pos].strip()

                            # IMPROVED: Check if the extracted text is just the applicant table
                            # If it contains "Job applicants as of" and doesn't have enough content, try to find the actual resume
                            if "Job applicants as of" in resume_text and len(resume_text.split('\n')) < 30:
                                # Search for the candidate's actual resume section
                                # Look for a section that starts with the candidate's name as a heading
                                candidate_section_pattern = f"# {re.escape(candidate_name)}\n"
                                candidate_section_match = re.search(candidate_section_pattern, content)

                                if candidate_section_match:
                                    start_pos = candidate_section_match.start()

                                    # Find the next heading after this position
                                    next_heading_match = re.search(r'\n# ', content[start_pos + len(candidate_section_pattern):])
                                    if next_heading_match:
                                        end_pos = start_pos + len(candidate_section_pattern) + next_heading_match.start()
                                    else:
                                        end_pos = len(content)

                                    # Extract the actual resume content
                                    resume_text = content[start_pos:end_pos].strip()
                                    logger.info(f"Found better resume content for {candidate_name} using name-based search")

                            # Store in the map
                            resume_map[candidate_name] = {
                                "text": resume_text,
                                "email": email
                            }

                            resume_found = True
                            logger.info(f"Found {candidate_name}'s resume using email search")

        if not resume_found:
            logger.warning(f"Could not find resume start for {candidate_name}, skipping")

    logger.info(f"Extracted {len(resume_map)} resumes from the text file")

    # Debug: Print the first few lines of each extracted resume
    if debug:
        logger.info("=== DEBUG: First 10 lines of each extracted resume ===")
        for candidate_name, resume_data in resume_map.items():
            resume_text = resume_data["text"]
            preview_lines = resume_text.split('\n')[:10]
            preview = '\n'.join(preview_lines)
            logger.info(f"--- {candidate_name} ---\n{preview}\n...")

    # Process each resume
    extracted_resumes = []

    for candidate_name, resume_data in resume_map.items():
        try:
            resume_text = resume_data["text"]
            email = resume_data["email"] or extract_email(resume_text)

            logger.info(f"Processing resume for {candidate_name}")

            # Extract contact information
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
                "summary": summary,
                "raw_text": resume_text  # Include the raw text for LLM processing
            }

            # Validate against schema
            try:
                # Create a copy without the raw_text field for validation
                validation_data = {k: v for k, v in resume_data.items() if k != "raw_text"}
                Resume(**validation_data)
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
            logger.error(f"Error processing resume for {candidate_name}: {e}")

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
    """Main function to run the script."""
    import argparse

    parser = argparse.ArgumentParser(description='Extract individual resumes from a processed text file.')
    parser.add_argument('--input-file', required=True, help='Path to the processed text file')
    parser.add_argument('--output-dir', required=True, help='Directory to save individual resume JSON files')
    parser.add_argument('--clean', action='store_true', help='Clean the output directory before extraction')
    parser.add_argument('--debug', action='store_true', help='Print debug information')
    args = parser.parse_args()

    # Clean the output directory if requested
    if args.clean:
        output_path = Path(args.output_dir)
        if output_path.exists():
            logger.info(f"Cleaning output directory: {args.output_dir}")
            # Remove all JSON files in the directory
            for file_path in output_path.glob('*.json'):
                file_path.unlink()
            logger.info(f"Output directory cleaned")

    # Extract resumes
    extract_resumes(args.input_file, args.output_dir, args.debug)

if __name__ == "__main__":
    main()
