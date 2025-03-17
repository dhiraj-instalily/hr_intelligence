#!/usr/bin/env python3
"""
MCP Server for HR Intelligence Database

This module implements a Model Context Protocol (MCP) server that exposes
the HR Intelligence database functionality as tools that can be used by
AI assistants or other clients.

The server provides tools for:
1. Searching for roles/responsibilities with fuzzy search
2. Performing semantic search across work experiences
3. Finding candidates with specific skill combinations
4. And more...

Usage:
    python mcp_server.py

The server will start and listen for MCP requests.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import MCP SDK
from mcp.server.fastmcp import FastMCP

# Import the fixed tool functions
from fixed_hr_tools import (
    search_by_role,
    semantic_search_experience,
    find_skill_combinations,
    get_candidate_details,
    search_by_education,
    close_db
)

from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create an MCP server
mcp = FastMCP("HR Intelligence", log_level="DEBUG")

# Register MCP tools
@mcp.tool()
def search_by_role_tool(keywords: str, company: str = None) -> List[Dict[str, Any]]:
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
    return search_by_role(keywords, company)

@mcp.tool()
def semantic_search_experience_tool(query: str) -> List[Dict[str, Any]]:
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
    return semantic_search_experience(query)

@mcp.tool()
def find_skill_combinations_tool(skills: List[str], match_all: bool = False) -> List[Dict[str, Any]]:
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
    return find_skill_combinations(skills, match_all)

@mcp.tool()
def get_candidate_details_tool(candidate_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific candidate.
    
    This tool retrieves the complete profile of a candidate by their ID,
    including all work experiences, education, skills, and other information.
    
    Args:
        candidate_id: Unique identifier of the candidate
        
    Returns:
        Complete candidate profile with all available information
    """
    return get_candidate_details(candidate_id)

@mcp.tool()
def search_by_education_tool(institution: str = None, degree: str = None) -> List[Dict[str, Any]]:
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
    return search_by_education(institution, degree)

def main():
    """Main entry point for the MCP server."""
    try:
        # Start the server
        mcp.run()
    finally:
        # Close database connection when the server stops
        close_db()

if __name__ == "__main__":
    main()