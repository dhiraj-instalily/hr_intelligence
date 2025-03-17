#!/usr/bin/env python3
"""
Script to use an LLM to extract structured information from resumes according to the schema.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.retrieval.schema import Resume

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

def get_llm_extraction(resume_text: str, schema_json: str) -> Dict[str, Any]:
    """
    Use an LLM to extract structured information from resume text according to the schema.

    Args:
        resume_text: The raw text of the resume
        schema_json: JSON string representation of the schema

    Returns:
        Dictionary containing the structured resume information
    """
    # Get API key from environment variable
    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise ValueError("LLAMA_CLOUD_API_KEY environment variable not set")

    # Construct the prompt for the LLM
    prompt = f"""
You are an expert resume parser. Extract structured information from the following resume text according to the provided schema.
Follow these guidelines:
1. Extract all relevant information that fits the schema
2. If information is not present in the resume, use null or empty lists as appropriate
3. Ensure the output is valid JSON that conforms to the schema
4. Be precise and accurate in your extraction

SCHEMA:
{schema_json}

RESUME TEXT:
{resume_text}

Return ONLY the JSON object with the extracted information. Do not include any explanations or additional text.
"""

    # Call the LLM API (using LlamaCloud API as an example)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {"role": "system", "content": "You are an expert resume parser that extracts structured information from resume text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,  # Low temperature for more deterministic output
        "max_tokens": 2000
    }

    try:
        response = requests.post(
            "https://api.llamacloud.ai/v1/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()

        # Extract the LLM's response
        result = response.json()
        llm_response = result["choices"][0]["message"]["content"]

        # Parse the JSON response
        # Find JSON object in the response (in case the LLM added any text before or after)
        import re
        json_match = re.search(r'({.*})', llm_response, re.DOTALL)
        if json_match:
            llm_response = json_match.group(1)

        extracted_data = json.loads(llm_response)
        return extracted_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling LLM API: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing LLM response as JSON: {e}")
        logger.error(f"LLM response: {llm_response}")
        raise

def process_resumes(input_dir: str, output_dir: str) -> None:
    """
    Process all resume JSON files in the input directory using an LLM.

    Args:
        input_dir: Directory containing extracted resume JSON files
        output_dir: Directory to save LLM-processed resume JSON files
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Get the schema as a JSON string
    schema_dict = Resume.schema()
    schema_json = json.dumps(schema_dict, indent=2)

    # Process each resume file
    input_path = Path(input_dir)
    resume_files = list(input_path.glob("*.json"))

    logger.info(f"Found {len(resume_files)} resume files to process")

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

            # Use LLM to extract structured information
            extracted_data = get_llm_extraction(resume_text, schema_json)

            # Validate against schema
            try:
                Resume(**extracted_data)
                logger.info(f"LLM-extracted resume for {candidate_name} validated successfully")
            except Exception as e:
                logger.warning(f"LLM-extracted resume for {candidate_name} failed validation: {e}")
                # Continue processing even if validation fails

            # Save to JSON file
            output_file = output_path / resume_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2)

            logger.info(f"Saved LLM-processed resume for {candidate_name} to {output_file}")

        except Exception as e:
            logger.error(f"Error processing resume file {resume_file}: {e}")

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Use an LLM to extract structured information from resumes.")
    parser.add_argument("--input-dir", type=str, default="data/extracted_resumes",
                        help="Directory containing extracted resume JSON files")
    parser.add_argument("--output-dir", type=str, default="data/llm_processed_resumes",
                        help="Directory to save LLM-processed resume JSON files")

    args = parser.parse_args()

    process_resumes(args.input_dir, args.output_dir)

if __name__ == "__main__":
    main()
