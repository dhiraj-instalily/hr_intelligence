#!/usr/bin/env python3
"""
Script to populate the hybrid database with extracted resumes.
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from tqdm import tqdm
import uuid

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.database.schema import Candidate, ContactInfo, Education, WorkExperience
from src.database.hybrid_search import HybridSearchHandler

logger = get_logger(__name__)

def convert_json_to_candidate(resume_data: Dict[str, Any]) -> Candidate:
    """
    Convert a resume JSON to a Candidate object.

    Args:
        resume_data: Resume data as a dictionary

    Returns:
        Candidate object
    """
    # Create contact info
    contact_info = ContactInfo(**resume_data.get("contact_info", {}))

    # Create education list
    education_list = []
    for edu_data in resume_data.get("education", []):
        # Set graduation_date to None to avoid date parsing issues
        edu_data["graduation_date"] = None
        education_list.append(Education(**edu_data))

    # Create work experience list
    work_experience_list = []
    for exp_data in resume_data.get("work_experience", []):
        # Handle date format issues - set to None to avoid date parsing
        exp_data["start_date"] = None
        exp_data["end_date"] = None

        # Add an ID field if missing
        if "id" not in exp_data:
            exp_data["id"] = str(uuid.uuid4())

        work_experience_list.append(WorkExperience(**exp_data))

    # Ensure certifications is a list
    certifications = resume_data.get("certifications", [])
    if certifications is None:
        certifications = []

    # Create candidate
    candidate = Candidate(
        candidate_name=resume_data.get("candidate_name", ""),
        document_type=resume_data.get("document_type", "resume"),
        contact_info=contact_info,
        education=education_list,
        work_experience=work_experience_list,
        skills=resume_data.get("skills", []),
        certifications=certifications,
        summary=resume_data.get("summary", None),
        raw_text=resume_data.get("raw_text", None)
    )

    return candidate

def populate_database(resumes_dir: str,
                      duckdb_path: str = "data/hr_database.duckdb",
                      chroma_path: str = "data/chroma_db") -> int:
    """
    Insert extracted resumes into the hybrid database.

    Args:
        resumes_dir: Directory containing extracted resume JSON files
        duckdb_path: Path to the DuckDB database file
        chroma_path: Path to the ChromaDB directory

    Returns:
        Number of resumes inserted into the database
    """
    # Initialize database handler
    db_handler = HybridSearchHandler(
        duckdb_path=duckdb_path,
        chroma_path=chroma_path
    )

    # Get all JSON files in the resumes directory
    resume_files = glob.glob(os.path.join(resumes_dir, "*.json"))
    logger.info(f"Found {len(resume_files)} resume JSON files in {resumes_dir}")

    # Insert each resume into the database
    inserted_count = 0

    for resume_file in tqdm(resume_files, desc="Inserting resumes"):
        try:
            # Load resume data
            with open(resume_file, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)

            # Get candidate name for logging
            candidate_name = resume_data.get('candidate_name', Path(resume_file).stem)
            logger.info(f"Inserting resume for {candidate_name} into database")

            # Convert to Candidate object
            candidate = convert_json_to_candidate(resume_data)

            # Insert into database
            db_handler.insert_candidate(candidate)
            logger.info(f"Successfully inserted resume for {candidate_name}")

            inserted_count += 1

        except Exception as e:
            logger.error(f"Error inserting resume {resume_file}: {e}")
            logger.exception(e)

    # Close database connection
    db_handler.close()

    logger.info(f"Successfully inserted {inserted_count} resumes into the database")
    return inserted_count

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Insert extracted resumes into the hybrid database")

    parser.add_argument(
        "--resumes-dir",
        type=str,
        default="data/llm_processed_resumes",
        help="Directory containing extracted resume JSON files"
    )

    parser.add_argument(
        "--duckdb-path",
        type=str,
        default="data/hr_database.duckdb",
        help="Path to the DuckDB database file"
    )

    parser.add_argument(
        "--chroma-path",
        type=str,
        default="data/chroma_db",
        help="Path to the ChromaDB directory"
    )

    args = parser.parse_args()

    # Populate database
    inserted_count = populate_database(
        args.resumes_dir,
        args.duckdb_path,
        args.chroma_path
    )

    print(f"Successfully inserted {inserted_count} resumes into the database")

    return 0

if __name__ == "__main__":
    sys.exit(main())
