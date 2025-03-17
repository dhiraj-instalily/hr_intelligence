#!/usr/bin/env python3
"""
Script to use an LLM to extract structured information from resumes according to the schema.
Uses GPT-4o with structured output from OpenAI.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from dotenv import load_dotenv
from openai import OpenAI
import re

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.retrieval.schema import Resume, Education, WorkExperience, ContactInfo

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

def get_llm_extraction(resume_text: str, schema_json: str, preview_only: bool = False) -> Dict[str, Any]:
    """
    Use GPT-4o to extract structured information from resume text according to the schema.
    Uses OpenAI's structured output feature for more reliable extraction.

    Args:
        resume_text: The raw text of the resume
        schema_json: JSON string representation of the schema
        preview_only: If True, only print the prompt and don't call the API

    Returns:
        Dictionary containing the structured resume information
    """
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and not preview_only:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Initialize OpenAI client
    if not preview_only:
        client = OpenAI(api_key=api_key)

    # Parse the schema JSON to include in the system message
    schema_dict = json.loads(schema_json)

    # System message with instructions and schema
    system_message = f"""
You are an expert resume parser. Extract structured information from the resume text according to the provided schema.

Schema:
```json
{json.dumps(schema_dict, indent=2)}
```

Follow these guidelines:
1. Extract all relevant information that fits the schema
2. If information is not present in the resume, use null or empty lists as appropriate
3. Be precise and accurate in your extraction
4. For education and work experience, extract dates in the format provided in the resume
5. For responsibilities, extract complete bullet points as separate items in the list
6. Your response must be a valid JSON object that conforms to the schema
7. The JSON object must include the following required fields: document_type, candidate_name, contact_info, education, work_experience, skills
"""

    user_message = f"Extract structured information from this resume:\n\n{resume_text}"

    # Print the prompt for preview
    logger.info("=== PROMPT PREVIEW ===")
    logger.info(f"System message:\n{system_message}")
    logger.info(f"User message:\n{user_message}")
    logger.info("=== END PROMPT PREVIEW ===")

    if preview_only:
        # Return a placeholder response for preview mode
        return {"preview_mode": True, "message": "Preview only - no API call made"}

    try:
        # Call the OpenAI API with structured output format
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.2,  # Low temperature for more deterministic output
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}
        )

        # Extract the structured response
        extracted_data = json.loads(response.choices[0].message.content)
        return extracted_data

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise

def process_resumes(input_dir: str, output_dir: str, preview_only: bool = False, max_previews: int = 3) -> None:
    """
    Process all resume JSON files in the input directory using GPT-4o.

    Args:
        input_dir: Directory containing extracted resume JSON files
        output_dir: Directory to save LLM-processed resume JSON files
        preview_only: If True, only print the prompts and don't call the API
        max_previews: Maximum number of prompts to preview
    """
    # This function is now replaced by the code in main()
    pass

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Use GPT-4o to extract structured information from resumes.")
    parser.add_argument("--input-dir", type=str, default="data/extracted_resumes",
                        help="Directory containing extracted resume JSON files")
    parser.add_argument("--output-dir", type=str, default="data/llm_processed_resumes",
                        help="Directory to save GPT-4o processed resume JSON files")
    parser.add_argument("--preview", action="store_true",
                        help="Preview mode: only print prompts, don't call the API")
    parser.add_argument("--max-previews", type=int, default=3,
                        help="Maximum number of prompts to preview in preview mode")
    parser.add_argument("--specific-file", type=str, default=None,
                        help="Process only a specific file in the input directory")

    args = parser.parse_args()

    # Process resumes
    input_path = Path(args.input_dir)

    # If a specific file is specified, only process that file
    if args.specific_file:
        resume_files = [input_path / args.specific_file]
        if not resume_files[0].exists():
            logger.error(f"Specified file {args.specific_file} not found in {args.input_dir}")
            return
        logger.info(f"Processing only the specified file: {args.specific_file}")
    else:
        # Process all resume files in the directory
        resume_files = list(input_path.glob("*.json"))
        logger.info(f"Found {len(resume_files)} resume files to process")

    # Ensure output directory exists
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Get the schema as a JSON string
    schema_dict = Resume.model_json_schema()  # Updated from schema() to model_json_schema()
    schema_json = json.dumps(schema_dict, indent=2)

    # Limit the number of previews if in preview mode
    if args.preview:
        if not args.specific_file:
            resume_files = resume_files[:args.max_previews]
        logger.info(f"Preview mode: showing prompts for {len(resume_files)} resumes")

    for resume_file in resume_files:
        try:
            # Read the resume file
            with open(resume_file, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)

            candidate_name = resume_data.get("candidate_name", "Unknown")
            logger.info(f"Processing resume for {candidate_name}")

            # Get the raw text of the resume
            resume_text = resume_data.get("raw_text", "")
            if not resume_text:
                logger.warning(f"No raw_text field found for {candidate_name}, using fallback method")
                # If raw_text field doesn't exist, convert the entire resume data to text
                # Remove the raw_text field if it exists to avoid circular references
                resume_data_copy = {k: v for k, v in resume_data.items() if k != "raw_text"}
                resume_text = json.dumps(resume_data_copy, indent=2)

            # IMPROVED: Clean up the raw text if it contains applicant tables
            if "Job applicants as of" in resume_text:
                logger.warning(f"Resume for {candidate_name} contains applicant tables, cleaning up")

                # Try to extract just the relevant section for this candidate
                candidate_section_pattern = f"# {re.escape(candidate_name)}\n"
                candidate_section_match = re.search(candidate_section_pattern, resume_text)

                if candidate_section_match:
                    start_pos = candidate_section_match.start()

                    # Find the next major heading after this position
                    next_heading_match = re.search(r'\n# [A-Z]', resume_text[start_pos + len(candidate_section_pattern):])
                    if next_heading_match:
                        end_pos = start_pos + len(candidate_section_pattern) + next_heading_match.start()
                        resume_text = resume_text[start_pos:end_pos].strip()
                    else:
                        # If no next heading, just use the rest of the text
                        resume_text = resume_text[start_pos:].strip()

                # If we couldn't find a section with the candidate's name, use the basic info we have
                if "Job applicants as of" in resume_text:
                    logger.warning(f"Could not find clean section for {candidate_name}, using basic info")
                    # Create a simplified resume text with just the basic info we know
                    resume_text = f"# {candidate_name}\n\nEmail: {resume_data.get('contact_info', {}).get('email', '')}\n"

                    # Add any other fields we have
                    if resume_data.get('contact_info', {}).get('phone'):
                        resume_text += f"Phone: {resume_data['contact_info']['phone']}\n"
                    if resume_data.get('contact_info', {}).get('linkedin'):
                        resume_text += f"LinkedIn: {resume_data['contact_info']['linkedin']}\n"

            # Use GPT-4o to extract structured information
            extracted_data = get_llm_extraction(resume_text, schema_json, args.preview)

            if args.preview:
                # Skip the rest in preview mode
                continue

            # Validate against schema
            try:
                Resume(**extracted_data)
                logger.info(f"GPT-4o extracted resume for {candidate_name} validated successfully")
            except Exception as e:
                logger.warning(f"GPT-4o extracted resume for {candidate_name} failed validation: {e}")
                # Continue processing even if validation fails

            # Save to JSON file
            output_file = output_path / resume_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2)

            logger.info(f"Saved GPT-4o processed resume for {candidate_name} to {output_file}")

        except Exception as e:
            logger.error(f"Error processing resume file {resume_file}: {e}")

if __name__ == "__main__":
    main()
