#!/usr/bin/env python3
"""
HR Intelligence Database Tool Functions

This module implements the core functionality for the HR Intelligence database tools
without the MCP server wrapper. These functions can be used directly or wrapped
in an MCP server.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import database components
from src.database.schema import SearchQuery, SearchResult
from src.database.hybrid_search import HybridSearchHandler
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Initialize the database handler
db_handler = HybridSearchHandler(
    duckdb_path="data/hr_database.duckdb",
    chroma_path="data/chroma_db"
)

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
    # Create a search query object
    query = SearchQuery(
        # Set the text field to None since we're not doing semantic search here
        text=None,
        # Set roles to the keywords for fuzzy search
        roles=[keywords],
        # Set companies filter if provided
        companies=[company] if company else None,
        # Use higher weight for fuzzy search since we're focusing on structured data
        fuzzy_weight=0.8,
        semantic_weight=0.2,
        # Default limit
        limit=10
    )
    
    # Log the search operation
    logger.info(f"Performing role search with keywords: {keywords}, company: {company}")
    
    # Execute the search using the hybrid search handler
    # This will primarily use the DuckDB fuzzy search capabilities
    results = db_handler.search(query)
    
    # Convert results to a serializable format
    serialized_results = []
    for result in results:
        # Extract relevant work experiences that match the search
        matching_experiences = []
        for exp in result.candidate.work_experience:
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
            serialized_results.append({
                "candidate_id": result.candidate.id,
                "candidate_name": result.candidate.candidate_name,
                "score": result.score,
                "matching_experiences": matching_experiences,
                "skills": result.candidate.skills[:10],  # Include top 10 skills
                "match_details": result.match_details
            })
    
    return serialized_results

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
    # Create a search query object focused on semantic search
    search_query = SearchQuery(
        # Set the text field for semantic search
        text=query,
        # Emphasize semantic search over fuzzy search
        semantic_weight=0.9,
        fuzzy_weight=0.1,
        # Default limit
        limit=10
    )
    
    # Log the search operation
    logger.info(f"Performing semantic search with query: {query}")
    
    # Execute the search using the hybrid search handler
    # This will primarily use the ChromaDB semantic search capabilities
    results = db_handler.search(search_query)
    
    # Convert results to a serializable format
    serialized_results = []
    for result in results:
        # Extract all work experiences for context
        experiences = []
        for exp in result.candidate.work_experience:
            experiences.append({
                "company": exp.company,
                "role": exp.role,
                "start_date": exp.start_date.isoformat() if exp.start_date else None,
                "end_date": exp.end_date.isoformat() if exp.end_date else None,
                "responsibilities": exp.responsibilities
            })
        
        serialized_results.append({
            "candidate_id": result.candidate.id,
            "candidate_name": result.candidate.candidate_name,
            "score": result.score,
            "semantic_score": result.match_details.get("semantic_score", 0),
            "experiences": experiences,
            "skills": result.candidate.skills[:10],  # Include top 10 skills
            "summary": result.candidate.summary
        })
    
    return serialized_results

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
    # Create a search query object
    query = SearchQuery(
        # Set the skills field for structured search
        skills=skills,
        # Use higher weight for fuzzy search since we're focusing on structured data
        fuzzy_weight=0.9,
        semantic_weight=0.1,
        # Default limit
        limit=20
    )
    
    # Log the search operation
    logger.info(f"Searching for candidates with skills: {skills}, match_all: {match_all}")
    
    # Execute the search using the hybrid search handler
    # This will primarily use the DuckDB structured search capabilities
    results = db_handler.search(query)
    
    # Filter results based on match_all parameter
    filtered_results = []
    for result in results:
        candidate_skills = set(result.candidate.skills)
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
            
        # Create a serializable result
        filtered_results.append({
            "candidate_id": result.candidate.id,
            "candidate_name": result.candidate.candidate_name,
            "score": result.score,
            "skills": list(candidate_skills),
            "matching_skills": list(candidate_skills.intersection(search_skills)),
            "match_percentage": match_percentage,
            # Include work experience summary
            "experience_summary": [
                {"company": exp.company, "role": exp.role}
                for exp in result.candidate.work_experience[:3]  # Top 3 experiences
            ]
        })
    
    # Sort by match percentage for more intuitive results
    filtered_results.sort(key=lambda x: x["match_percentage"], reverse=True)
    
    return filtered_results

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
    candidate = db_handler.get_candidate(candidate_id)
    
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
    # Create a search query object
    query = SearchQuery(
        # Set the education field for structured search
        education=[institution] if institution else None,
        # Use higher weight for fuzzy search since we're focusing on structured data
        fuzzy_weight=0.8,
        semantic_weight=0.2,
        # Default limit
        limit=10
    )
    
    # Log the search operation
    logger.info(f"Searching for candidates with education: institution={institution}, degree={degree}")
    
    # Execute the search using the hybrid search handler
    results = db_handler.search(query)
    
    # Filter and format results
    serialized_results = []
    for result in results:
        # Filter education entries based on degree if specified
        matching_education = []
        for edu in result.candidate.education:
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
            serialized_results.append({
                "candidate_id": result.candidate.id,
                "candidate_name": result.candidate.candidate_name,
                "score": result.score,
                "matching_education": matching_education,
                "skills": result.candidate.skills[:10],  # Include top 10 skills
                # Include brief work history
                "experience_summary": [
                    {"company": exp.company, "role": exp.role}
                    for exp in result.candidate.work_experience[:2]  # Top 2 experiences
                ]
            })
    
    return serialized_results

def close_db():
    """Close the database connection."""
    db_handler.close()
    logger.info("Database connections closed")