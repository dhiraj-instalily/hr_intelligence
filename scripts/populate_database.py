#!/usr/bin/env python3
"""
Script to insert extracted resumes into the database.
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.ingestion.database_handler import DatabaseHandler
from src.utils.helpers import load_config

logger = get_logger(__name__)

def populate_database(resumes_dir: str, config_path: str) -> int:
    """
    Insert extracted resumes into the database.

    Args:
        resumes_dir: Directory containing extracted resume JSON files
        config_path: Path to the configuration file

    Returns:
        Number of resumes inserted into the database
    """
    # Load configuration
    config = load_config(config_path)
    if not config:
        logger.error("Failed to load configuration")
        return 0

    # Initialize database handler
    db_handler = DatabaseHandler(config.get('database', {}))

    # Get all JSON files in the resumes directory
    resume_files = glob.glob(os.path.join(resumes_dir, "*.json"))
    logger.info(f"Found {len(resume_files)} resume JSON files in {resumes_dir}")

    # Insert each resume into the database
    inserted_count = 0

    for resume_file in resume_files:
        try:
            # Load resume data
            with open(resume_file, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)

            # Get candidate name for logging
            candidate_name = resume_data.get('candidate_name', Path(resume_file).stem)
            logger.info(f"Inserting resume for {candidate_name} into database")

            # Insert into database
            document_type = resume_data.get('document_type', 'resume')
            original_file = f"{candidate_name.replace(' ', '_')}.pdf"  # Simulated original file name

            db_handler.insert_document(document_type, original_file, resume_data)
            logger.info(f"Successfully inserted resume for {candidate_name}")

            inserted_count += 1

        except Exception as e:
            logger.error(f"Error inserting resume {resume_file}: {e}")

    # Close database connection
    db_handler.close()

    logger.info(f"Successfully inserted {inserted_count} resumes into the database")
    return inserted_count

def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Insert extracted resumes into the database")

    parser.add_argument(
        "--resumes-dir",
        type=str,
        default="data/extracted_resumes",
        help="Directory containing extracted resume JSON files"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file"
    )

    args = parser.parse_args()

    # Populate database
    inserted_count = populate_database(args.resumes_dir, args.config)

    print(f"Successfully inserted {inserted_count} resumes into the database")

    return 0

if __name__ == "__main__":
    sys.exit(main())
