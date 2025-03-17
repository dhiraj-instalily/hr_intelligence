#!/usr/bin/env python3
"""
Test script with fixed database handler
"""

import sys
import json
import duckdb
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import database components
from src.database.schema import Candidate, SearchQuery
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)
console = Console()

def get_candidate(conn, candidate_id: str) -> Optional[Candidate]:
    """
    Retrieve a candidate from the database by ID.

    Args:
        conn: DuckDB connection
        candidate_id: ID of the candidate to retrieve

    Returns:
        Candidate object, or None if not found
    """
    # Get column names
    columns = conn.execute("SELECT * FROM candidates LIMIT 0").description
    column_names = [col[0] for col in columns]
    
    # Get candidate data
    result = conn.execute(
        "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
    ).fetchone()

    if not result:
        return None

    # Convert to dictionary using column names
    candidate_dict = dict(zip(column_names, result))

    # Parse JSON fields
    candidate_dict["contact_info"] = json.loads(candidate_dict["contact_info"])
    candidate_dict["education"] = json.loads(candidate_dict["education"])
    candidate_dict["work_experience"] = json.loads(candidate_dict["work_experience"])
    candidate_dict["skills"] = json.loads(candidate_dict["skills"])
    candidate_dict["certifications"] = json.loads(candidate_dict["certifications"])

    # Convert to Candidate object
    return Candidate(**candidate_dict)

def main():
    """Main entry point for the test script."""
    console.print("[bold]HR Intelligence Database Test (Fixed)[/bold]")
    
    try:
        # Connect to DuckDB
        db_path = "data/hr_database.duckdb"
        conn = duckdb.connect(db_path)
        
        # Get all candidate IDs
        candidate_ids = conn.execute("SELECT id FROM candidates LIMIT 5").fetchall()
        
        if not candidate_ids:
            console.print("[bold red]No candidates found in the database[/bold red]")
            return 1
            
        # Get the first candidate
        candidate_id = candidate_ids[0][0]
        console.print(f"Testing with candidate ID: {candidate_id}")
        
        # Get candidate
        candidate = get_candidate(conn, candidate_id)
        
        if not candidate:
            console.print(f"[bold red]Candidate with ID {candidate_id} not found[/bold red]")
            return 1
            
        # Display candidate information
        console.print(f"\n[bold green]Candidate:[/bold green] {candidate.candidate_name}")
        
        # Skills
        console.print("\n[bold]Skills:[/bold]")
        console.print(", ".join(candidate.skills[:10]))
        
        # Work Experience
        console.print("\n[bold]Work Experience:[/bold]")
        for exp in candidate.work_experience[:2]:
            console.print(f"\n[bold cyan]{exp.role}[/bold cyan] at [bold magenta]{exp.company}[/bold magenta]")
            
        # Education
        console.print("\n[bold]Education:[/bold]")
        for edu in candidate.education[:2]:
            console.print(f"\n[bold cyan]{edu.degree}[/bold cyan] at [bold magenta]{edu.institution}[/bold magenta]")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())