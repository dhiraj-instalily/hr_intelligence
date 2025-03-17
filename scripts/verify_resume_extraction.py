#!/usr/bin/env python3
"""
Script to verify the extraction of individual resumes by creating a mapping from candidate names to raw text.
This helps confirm that all candidates are correctly identified and their resume text is properly extracted.

Known Issues:
1. Some candidates with name variations (e.g., "Nimeesh Bagwe" vs "NIMEESH NILESH BAGWE") are not being properly extracted
2. Non-candidate headings like "COMMUNITY_INVOLVEMENT", "PROFESSIONAL_EXPERIENCE", etc. are incorrectly being extracted as candidates
3. Candidates with special characters or different formatting in their names may be missed

Future Improvements:
1. Enhance the name matching algorithm to be case-insensitive and support partial matching
2. Implement a filtering mechanism to exclude non-candidate headings based on context
3. Add validation against the original candidate table to ensure only real candidates are extracted
4. Consider using fuzzy matching for names with slight variations
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger

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

def create_name_to_text_map(text_file_path: str) -> Dict[str, str]:
    """
    Create a mapping from candidate names to their raw resume text.

    Args:
        text_file_path: Path to the processed text file

    Returns:
        Dictionary mapping candidate names to their raw resume text
    """
    # Read the processed text file
    with open(text_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract candidate names and emails from the tables at the beginning
    candidates = extract_candidate_names_from_table(content)

    if not candidates:
        logger.warning("No candidates found in the tables. Falling back to regex pattern matching.")
        # Fallback to the old method if no candidates are found in tables
        name_pattern = r'# ([A-Za-z]+ [A-Za-z]+)\n'
        names = re.findall(name_pattern, content)
        # Filter out non-candidate names (like section headers)
        candidates = [(name, "") for name in names if len(name.split()) == 2]

    # Create a map to store resume content for each candidate
    name_to_text_map = {}

    # Find the start of each resume by looking for the candidate's name as a heading
    for i, (candidate_name, email) in enumerate(candidates):
        # Escape special characters in the name for regex
        escaped_name = re.escape(candidate_name)

        # Find the start of this candidate's resume
        resume_start_pattern = rf'# {escaped_name}\n'
        start_match = re.search(resume_start_pattern, content)

        if not start_match:
            logger.warning(f"Could not find resume start for {candidate_name}, skipping")
            continue

        start_pos = start_match.start()

        # Find the start of the next candidate's resume (if any)
        end_pos = len(content)
        if i < len(candidates) - 1:
            next_candidate, _ = candidates[i + 1]
            escaped_next_name = re.escape(next_candidate)
            next_start_pattern = rf'# {escaped_next_name}\n'
            next_start_match = re.search(next_start_pattern, content)
            if next_start_match:
                end_pos = next_start_match.start()

        # Extract the resume content
        resume_text = content[start_pos:end_pos].strip()

        # Store in the map
        name_to_text_map[candidate_name] = resume_text

    logger.info(f"Created mapping for {len(name_to_text_map)} candidates")
    return name_to_text_map

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Verify resume extraction by creating a name-to-text mapping.")
    parser.add_argument("--input-file", type=str, required=True,
                        help="Path to the processed text file")
    parser.add_argument("--output-file", type=str, required=True,
                        help="Path to save the name-to-text mapping JSON file")

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    output_path = Path(args.output_file)
    output_path.parent.mkdir(exist_ok=True, parents=True)

    # Create the name-to-text mapping
    name_to_text_map = create_name_to_text_map(args.input_file)

    # Save the mapping to a JSON file
    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(name_to_text_map, f, indent=2)

    logger.info(f"Saved name-to-text mapping to {args.output_file}")
    logger.info(f"Extracted {len(name_to_text_map)} candidate resumes")

    # Print the names of extracted candidates for quick verification
    print("\nExtracted candidates:")
    for i, name in enumerate(name_to_text_map.keys(), 1):
        print(f"{i}. {name}")

if __name__ == "__main__":
    main()
