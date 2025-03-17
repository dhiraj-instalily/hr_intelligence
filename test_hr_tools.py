#!/usr/bin/env python3
"""
Test script for HR Intelligence tool functions

This script tests the tool functions directly to verify that they work as expected.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the tool functions
from hr_tools import (
    search_by_role,
    semantic_search_experience,
    find_skill_combinations,
    get_candidate_details,
    search_by_education,
    close_db
)

# Initialize console for pretty printing
console = Console()

def display_candidates(candidates, title="Search Results"):
    """
    Display candidates in a formatted table.
    
    Args:
        candidates: List of candidate dictionaries
        title: Title for the table
    """
    if not candidates:
        console.print("[bold red]No results found[/bold red]")
        return

    table = Table(title=title)

    table.add_column("Name", style="green")
    table.add_column("Skills", style="yellow")
    table.add_column("Experience", style="magenta")
    
    if "score" in candidates[0]:
        table.add_column("Score", justify="right", style="cyan")

    for candidate in candidates:
        # Format skills
        skills = ", ".join(candidate.get("skills", [])[:5])
        if len(candidate.get("skills", [])) > 5:
            skills += f" (+{len(candidate.get('skills', [])) - 5} more)"

        # Format experience
        experience = []
        
        # Check which field contains experience data
        if "matching_experiences" in candidate:
            exp_list = candidate["matching_experiences"]
        elif "experiences" in candidate:
            exp_list = candidate["experiences"]
        elif "experience_summary" in candidate:
            exp_list = candidate["experience_summary"]
        else:
            exp_list = []
            
        for exp in exp_list[:2]:
            if "company" in exp and "role" in exp:
                experience.append(f"{exp['role']} at {exp['company']}")

        experience_str = "\n".join(experience)
        if len(exp_list) > 2:
            experience_str += f"\n(+{len(exp_list) - 2} more)"

        # Add row
        if "score" in candidate:
            table.add_row(
                candidate.get("candidate_name", ""),
                skills,
                experience_str,
                f"{candidate.get('score', 0):.2f}"
            )
        else:
            table.add_row(
                candidate.get("candidate_name", ""),
                skills,
                experience_str
            )

    console.print(table)

def test_role_search():
    """Test searching by role."""
    console.print("\n[bold blue]Test 1: Search by Role[/bold blue]")
    
    # Call the tool function directly
    results = search_by_role(keywords="software engineer")
    
    # Display results
    display_candidates(results, "Software Engineers")
    
    # Return first candidate ID for later tests
    return results[0]["candidate_id"] if results else None

def test_semantic_search():
    """Test semantic search."""
    console.print("\n[bold blue]Test 2: Semantic Search[/bold blue]")
    
    # Call the tool function directly
    results = semantic_search_experience(query="Experience with data analysis and visualization")
    
    # Display results
    display_candidates(results, "Data Analysis Experience")

def test_skill_search():
    """Test searching by skills."""
    console.print("\n[bold blue]Test 3: Skill Combinations[/bold blue]")
    
    # Call the tool function directly
    results = find_skill_combinations(skills=["Python", "JavaScript"])
    
    # Display results
    display_candidates(results, "Candidates with Python OR JavaScript")

def test_education_search():
    """Test searching by education."""
    console.print("\n[bold blue]Test 4: Education Search[/bold blue]")
    
    # Call the tool function directly
    results = search_by_education(degree="Computer Science")
    
    # Display results
    display_candidates(results, "Computer Science Graduates")

def test_candidate_details(candidate_id):
    """Test getting candidate details."""
    console.print("\n[bold blue]Test 5: Candidate Details[/bold blue]")
    
    if not candidate_id:
        console.print("[bold red]No candidate ID available for testing[/bold red]")
        return
    
    # Call the tool function directly
    details = get_candidate_details(candidate_id=candidate_id)
    
    # Display detailed information
    console.print(f"[bold green]Candidate:[/bold green] {details.get('name', 'Unknown')}")
    
    # Contact info
    contact = details.get("contact_info", {})
    console.print("\n[bold]Contact Information:[/bold]")
    console.print(f"Email: {contact.get('email', 'N/A')}")
    console.print(f"Phone: {contact.get('phone', 'N/A')}")
    console.print(f"LinkedIn: {contact.get('linkedin', 'N/A')}")
    
    # Summary
    if details.get("summary"):
        console.print(f"\n[bold]Summary:[/bold]\n{details.get('summary')}")
    
    # Skills
    console.print("\n[bold]Skills:[/bold]")
    console.print(", ".join(details.get("skills", [])))
    
    # Work Experience
    console.print("\n[bold]Work Experience:[/bold]")
    for exp in details.get("work_experience", []):
        console.print(f"\n[bold cyan]{exp.get('role')}[/bold cyan] at [bold magenta]{exp.get('company')}[/bold magenta]")
        dates = []
        if exp.get("start_date"):
            dates.append(exp.get("start_date"))
        if exp.get("end_date"):
            dates.append(exp.get("end_date"))
        if dates:
            console.print(f"Dates: {' - '.join(dates)}")
        
        console.print("Responsibilities:")
        for resp in exp.get("responsibilities", []):
            console.print(f"• {resp}")
    
    # Education
    console.print("\n[bold]Education:[/bold]")
    for edu in details.get("education", []):
        console.print(f"\n[bold cyan]{edu.get('degree')}[/bold cyan] at [bold magenta]{edu.get('institution')}[/bold magenta]")
        if edu.get("graduation_date"):
            console.print(f"Graduation: {edu.get('graduation_date')}")
        if edu.get("gpa"):
            console.print(f"GPA: {edu.get('gpa')}")

def main():
    """Main entry point for the test script."""
    console.print("[bold]HR Intelligence Tool Functions Test[/bold]")
    console.print("This script tests the tool functions directly.")
    
    try:
        # Run tests
        candidate_id = test_role_search()
        test_semantic_search()
        test_skill_search()
        test_education_search()
        test_candidate_details(candidate_id)
        
        # Close database connection
        close_db()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())