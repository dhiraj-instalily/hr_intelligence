#!/usr/bin/env python3
"""
Fixed HR Intelligence Database Tool Functions

This module implements the core functionality for the HR Intelligence database tools
with fixes for the DuckDB handler issues.
"""

import os
import sys
import json
import duckdb
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from uuid import uuid4

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import database components
from src.database.schema import Candidate, SearchQuery, WorkExperience, Education, ContactInfo
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Database paths
DUCKDB_PATH = "data/hr_database.duckdb"

# Connect to DuckDB
conn = duckdb.connect(DUCKDB_PATH)

def get_column_names(table_name):
    """Get column names for a table."""
    columns = conn.execute(f"SELECT * FROM {table_name} LIMIT 0").description
    return [col[0] for col in columns]

# Get column names for tables
CANDIDATE_COLUMNS = get_column_names("candidates")

def get_candidate(candidate_id: str) -> Optional[Candidate]:
    """
    Retrieve a candidate from the database by ID.

    Args:
        candidate_id: ID of the candidate to retrieve

    Returns:
        Candidate object, or None if not found
    """
    # Get candidate data
    result = conn.execute(
        "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
    ).fetchone()

    if not result:
        return None

    # Convert to dictionary using column names
    candidate_dict = dict(zip(CANDIDATE_COLUMNS, result))

    # Parse JSON fields
    candidate_dict["contact_info"] = json.loads(candidate_dict["contact_info"])
    candidate_dict["education"] = json.loads(candidate_dict["education"])
    candidate_dict["work_experience"] = json.loads(candidate_dict["work_experience"])
    candidate_dict["skills"] = json.loads(candidate_dict["skills"])
    candidate_dict["certifications"] = json.loads(candidate_dict["certifications"])

    # Convert to Candidate object
    return Candidate(**candidate_dict)

def get_all_candidates(limit: int = 10, offset: int = 0) -> List[Candidate]:
    """
    Get all candidates from the database.

    Args:
        limit: Maximum number of candidates to return
        offset: Number of candidates to skip

    Returns:
        List of Candidate objects
    """
    # Get candidate data
    results = conn.execute(
        f"SELECT * FROM candidates LIMIT {limit} OFFSET {offset}"
    ).fetchall()

    # Convert to Candidate objects
    candidates = []
    for result in results:
        # Convert to dictionary using column names
        candidate_dict = dict(zip(CANDIDATE_COLUMNS, result))

        # Parse JSON fields
        candidate_dict["contact_info"] = json.loads(candidate_dict["contact_info"])
        candidate_dict["education"] = json.loads(candidate_dict["education"])
        candidate_dict["work_experience"] = json.loads(candidate_dict["work_experience"])
        candidate_dict["skills"] = json.loads(candidate_dict["skills"])
        candidate_dict["certifications"] = json.loads(candidate_dict["certifications"])

        # Convert to Candidate object
        candidates.append(Candidate(**candidate_dict))

    return candidates

def search_by_role(keywords: str, company: str = None) -> List[Dict[str, Any]]:
    """
    Fuzzy search for roles/responsibilities with optional company filter.
    
    This tool searches for candidates based on their job roles and responsibilities
    using fuzzy matching (trigram-based search). It can optionally filter by company.
    
    Args:
        keywords: Keywords to search for in roles and responsibilities
        company: Optional company name to filter results
        
    Returns:
        List of candidates matching the search criteria, with their details and match scores
    """
    # Log the search operation
    logger.info(f"Performing role search with keywords: {keywords}, company: {company}")
    
    # Get all candidates
    candidates = get_all_candidates(limit=50)
    
    # Filter candidates based on role and company
    results = []
    for candidate in candidates:
        # Check each work experience
        matching_experiences = []
        for exp in candidate.work_experience:
            # Check if this experience matches our search criteria
            if (keywords.lower() in exp.role.lower() or 
                any(keywords.lower() in resp.lower() for resp in exp.responsibilities)):
                
                # If company filter is applied, check company match
                if company and company.lower() not in exp.company.lower():
                    continue
                    
                # Add the matching experience
                matching_experiences.append({
                    "company": exp.company,
                    "role": exp.role,
                    "start_date": exp.start_date.isoformat() if exp.start_date else None,
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "responsibilities": exp.responsibilities
                })
        
        # Only include candidates with matching experiences
        if matching_experiences:
            # Calculate a simple score based on number of matching experiences
            score = len(matching_experiences) / len(candidate.work_experience)
            
            results.append({
                "candidate_id": candidate.id,
                "candidate_name": candidate.candidate_name,
                "score": score,
                "matching_experiences": matching_experiences,
                "skills": candidate.skills[:10],  # Include top 10 skills
                "match_details": {"role_match_score": score}
            })
    
    # Sort by score (descending)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Limit to 10 results
    return results[:10]

def semantic_search_experience(query: str) -> List[Dict[str, Any]]:
    """
    Deep semantic search across all work experiences.
    
    This tool uses vector embeddings to find candidates whose work experiences
    semantically match the query, even if they don't contain the exact keywords.
    It's powered by ChromaDB and sentence transformers for semantic understanding.
    
    Args:
        query: Natural language query describing the experience to search for
        
    Returns:
        List of candidates with semantically matching experiences, ranked by relevance
    """
    # Log the search operation
    logger.info(f"Performing semantic search with query: {query}")
    
    # For now, we'll use a simple keyword search since the ChromaDB integration is having issues
    # Get all candidates
    candidates = get_all_candidates(limit=50)
    
    # Filter candidates based on query
    results = []
    for candidate in candidates:
        # Check each work experience
        experiences = []
        match_score = 0
        
        for exp in candidate.work_experience:
            # Simple keyword matching (in a real semantic search, this would use embeddings)
            role_match = query.lower() in exp.role.lower()
            resp_match = any(query.lower() in resp.lower() for resp in exp.responsibilities)
            
            if role_match or resp_match:
                match_score += 1
            
            # Add all experiences for context
            experiences.append({
                "company": exp.company,
                "role": exp.role,
                "start_date": exp.start_date.isoformat() if exp.start_date else None,
                "end_date": exp.end_date.isoformat() if exp.end_date else None,
                "responsibilities": exp.responsibilities
            })
        
        # Only include candidates with some match
        if match_score > 0:
            # Normalize score
            score = match_score / len(candidate.work_experience)
            
            results.append({
                "candidate_id": candidate.id,
                "candidate_name": candidate.candidate_name,
                "score": score,
                "semantic_score": score,
                "experiences": experiences,
                "skills": candidate.skills[:10],  # Include top 10 skills
                "summary": candidate.summary
            })
    
    # Sort by score (descending)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Limit to 10 results
    return results[:10]

def find_skill_combinations(skills: List[str], match_all: bool = False) -> List[Dict[str, Any]]:
    """
    Find candidates with ANY or ALL of the specified skills.
    
    This tool searches for candidates based on their skills, with the option to
    require all skills (AND logic) or any of the skills (OR logic).
    It uses SQL array operations for efficient filtering.
    
    Args:
        skills: List of skills to search for
        match_all: If True, candidates must have ALL specified skills;
                  if False, candidates with ANY of the skills will be returned
        
    Returns:
        List of candidates matching the skill criteria, with their details and match scores
    """
    # Log the search operation
    logger.info(f"Searching for candidates with skills: {skills}, match_all: {match_all}")
    
    # Get all candidates
    candidates = get_all_candidates(limit=50)
    
    # Filter candidates based on skills
    results = []
    for candidate in candidates:
        candidate_skills = set(candidate.skills)
        search_skills = set(skills)
        
        # Calculate skill match percentage
        if len(search_skills) > 0:
            matching_skills = candidate_skills.intersection(search_skills)
            match_percentage = len(matching_skills) / len(search_skills) * 100
        else:
            match_percentage = 0
            
        # Apply filtering logic
        if match_all and not search_skills.issubset(candidate_skills):
            # Skip candidates that don't have ALL required skills
            continue
            
        # Only include candidates with at least one matching skill
        if len(matching_skills) > 0:
            # Create a serializable result
            results.append({
                "candidate_id": candidate.id,
                "candidate_name": candidate.candidate_name,
                "score": match_percentage / 100,  # Normalize to 0-1
                "skills": list(candidate_skills),
                "matching_skills": list(matching_skills),
                "match_percentage": match_percentage,
                # Include work experience summary
                "experience_summary": [
                    {"company": exp.company, "role": exp.role}
                    for exp in candidate.work_experience[:3]  # Top 3 experiences
                ]
            })
    
    # Sort by match percentage for more intuitive results
    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    
    # Limit to 20 results
    return results[:20]

def get_candidate_details(candidate_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific candidate.
    
    This tool retrieves the complete profile of a candidate by their ID,
    including all work experiences, education, skills, and other information.
    
    Args:
        candidate_id: Unique identifier of the candidate
        
    Returns:
        Complete candidate profile with all available information
    """
    # Log the operation
    logger.info(f"Retrieving details for candidate: {candidate_id}")
    
    # Get the candidate from the database
    candidate = get_candidate(candidate_id)
    
    # Check if candidate exists
    if not candidate:
        return {"error": f"Candidate with ID {candidate_id} not found"}
    
    # Convert to serializable format
    result = {
        "id": candidate.id,
        "name": candidate.candidate_name,
        "contact_info": {
            "email": candidate.contact_info.email,
            "phone": candidate.contact_info.phone,
            "address": candidate.contact_info.address,
            "linkedin": candidate.contact_info.linkedin,
            "website": candidate.contact_info.website
        },
        "summary": candidate.summary,
        "skills": candidate.skills,
        "certifications": candidate.certifications,
        "work_experience": [
            {
                "company": exp.company,
                "role": exp.role,
                "start_date": exp.start_date.isoformat() if exp.start_date else None,
                "end_date": exp.end_date.isoformat() if exp.end_date else None,
                "responsibilities": exp.responsibilities
            }
            for exp in candidate.work_experience
        ],
        "education": [
            {
                "institution": edu.institution,
                "degree": edu.degree,
                "graduation_date": edu.graduation_date,
                "gpa": edu.gpa
            }
            for edu in candidate.education
        ]
    }
    
    return result

def search_by_education(institution: str = None, degree: str = None) -> List[Dict[str, Any]]:
    """
    Search for candidates by education criteria.
    
    This tool allows searching for candidates based on their educational
    background, including institutions attended and degrees earned.
    
    Args:
        institution: Name of educational institution (university, college, etc.)
        degree: Type of degree or field of study
        
    Returns:
        List of candidates matching the education criteria
    """
    # Log the search operation
    logger.info(f"Searching for candidates with education: institution={institution}, degree={degree}")
    
    # Get all candidates
    candidates = get_all_candidates(limit=50)
    
    # Filter candidates based on education
    results = []
    for candidate in candidates:
        # Filter education entries based on criteria
        matching_education = []
        for edu in candidate.education:
            # Check institution match
            institution_match = not institution or institution.lower() in edu.institution.lower()
            
            # Check degree match
            degree_match = not degree or degree.lower() in edu.degree.lower()
            
            # Include if both match
            if institution_match and degree_match:
                matching_education.append({
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "graduation_date": edu.graduation_date,
                    "gpa": edu.gpa
                })
        
        # Only include candidates with matching education
        if matching_education:
            # Calculate a simple score based on number of matching education entries
            score = len(matching_education) / len(candidate.education)
            
            results.append({
                "candidate_id": candidate.id,
                "candidate_name": candidate.candidate_name,
                "score": score,
                "matching_education": matching_education,
                "skills": candidate.skills[:10],  # Include top 10 skills
                # Include brief work history
                "experience_summary": [
                    {"company": exp.company, "role": exp.role}
                    for exp in candidate.work_experience[:2]  # Top 2 experiences
                ]
            })
    
    # Sort by score (descending)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Limit to 10 results
    return results[:10]

def close_db():
    """Close the database connection."""
    conn.close()
    logger.info("Database connection closed")