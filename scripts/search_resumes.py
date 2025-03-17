#!/usr/bin/env python3
"""
Script to search for resumes using the hybrid search capabilities.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from rich.console import Console
from rich.table import Table

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.database.schema import SearchQuery
from src.database.hybrid_search import HybridSearchHandler

logger = get_logger(__name__)
console = Console()

def display_search_results(results, verbose=False):
    """
    Display search results in a formatted table.

    Args:
        results: List of search results
        verbose: Whether to display detailed information
    """
    if not results:
        console.print("[bold red]No results found[/bold red]")
        return

    table = Table(title="Search Results")

    table.add_column("Score", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Skills", style="yellow")
    table.add_column("Experience", style="magenta")

    if verbose:
        table.add_column("Match Details", style="blue")

    for result in results:
        candidate = result.candidate

        # Format skills
        skills = ", ".join(candidate.skills[:5])
        if len(candidate.skills) > 5:
            skills += f" (+{len(candidate.skills) - 5} more)"

        # Format experience
        experience = []
        for exp in candidate.work_experience[:2]:
            experience.append(f"{exp.role} at {exp.company}")

        experience_str = "\n".join(experience)
        if len(candidate.work_experience) > 2:
            experience_str += f"\n(+{len(candidate.work_experience) - 2} more)"

        # Format match details
        match_details = ""
        if verbose:
            for key, value in result.match_details.items():
                match_details += f"{key}: {value:.2f}\n"

        # Add row
        if verbose:
            table.add_row(
                f"{result.score:.2f}",
                candidate.candidate_name,
                skills,
                experience_str,
                match_details
            )
        else:
            table.add_row(
                f"{result.score:.2f}",
                candidate.candidate_name,
                skills,
                experience_str
            )

    console.print(table)

def search_resumes(query_text: Optional[str] = None,
                   skills: Optional[List[str]] = None,
                   companies: Optional[List[str]] = None,
                   roles: Optional[List[str]] = None,
                   education: Optional[List[str]] = None,
                   limit: int = 10,
                   duckdb_path: str = "data/hr_database.duckdb",
                   chroma_path: str = "data/chroma_db",
                   verbose: bool = False):
    """
    Search for resumes using the hybrid search capabilities.

    Args:
        query_text: Free text query for semantic search
        skills: List of skills to search for
        companies: List of companies to search for
        roles: List of roles to search for
        education: List of education institutions to search for
        limit: Maximum number of results to return
        duckdb_path: Path to the DuckDB database file
        chroma_path: Path to the ChromaDB directory
        verbose: Whether to display detailed information
    """
    # Initialize database handler
    db_handler = HybridSearchHandler(
        duckdb_path=duckdb_path,
        chroma_path=chroma_path
    )

    # Create search query
    search_query = SearchQuery(
        text=query_text,
        skills=skills,
        companies=companies,
        roles=roles,
        education=education,
        limit=limit
    )

    # Perform search
    results = db_handler.search(search_query)

    # Display results
    display_search_results(results, verbose)

    # Close database connection
    db_handler.close()

    return results

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Search for resumes using the hybrid search capabilities")

    parser.add_argument(
        "--query",
        type=str,
        help="Free text query for semantic search"
    )

    parser.add_argument(
        "--skills",
        type=str,
        nargs="+",
        help="List of skills to search for"
    )

    parser.add_argument(
        "--companies",
        type=str,
        nargs="+",
        help="List of companies to search for"
    )

    parser.add_argument(
        "--roles",
        type=str,
        nargs="+",
        help="List of roles to search for"
    )

    parser.add_argument(
        "--education",
        type=str,
        nargs="+",
        help="List of education institutions to search for"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results to return"
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

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Display detailed information"
    )

    args = parser.parse_args()

    # Check if at least one search parameter is provided
    if not any([args.query, args.skills, args.companies, args.roles, args.education]):
        parser.error("At least one search parameter must be provided")

    # Search for resumes
    search_resumes(
        query_text=args.query,
        skills=args.skills,
        companies=args.companies,
        roles=args.roles,
        education=args.education,
        limit=args.limit,
        duckdb_path=args.duckdb_path,
        chroma_path=args.chroma_path,
        verbose=args.verbose
    )

    return 0

if __name__ == "__main__":
    sys.exit(main())
