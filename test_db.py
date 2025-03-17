#!/usr/bin/env python3
"""
Test script for directly querying the database
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import database components
from src.database.schema import SearchQuery
from src.database.hybrid_search import HybridSearchHandler
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)
console = Console()

def main():
    """Main entry point for the test script."""
    console.print("[bold]HR Intelligence Database Test[/bold]")
    
    try:
        # Initialize database handler
        db_handler = HybridSearchHandler(
            duckdb_path="data/hr_database.duckdb",
            chroma_path="data/chroma_db"
        )
        
        # Create a simple search query
        query = SearchQuery(
            text="software engineer",
            limit=5
        )
        
        # Execute the search
        console.print("\n[bold]Executing search query...[/bold]")
        results = db_handler.search(query)
        
        # Display results
        console.print(f"\n[bold]Found {len(results)} results[/bold]")
        
        for i, result in enumerate(results):
            console.print(f"\n[bold cyan]Result {i+1}:[/bold cyan]")
            console.print(f"Candidate: {result.candidate.candidate_name}")
            console.print(f"Score: {result.score}")
            console.print(f"Skills: {', '.join(result.candidate.skills[:5])}")
            
            # Show first work experience
            if result.candidate.work_experience:
                exp = result.candidate.work_experience[0]
                console.print(f"Experience: {exp.role} at {exp.company}")
        
        # Close database connection
        db_handler.close()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())