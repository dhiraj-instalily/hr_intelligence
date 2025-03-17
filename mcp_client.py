#!/usr/bin/env python3
"""
Simple MCP client to test the HR Intelligence MCP server
"""

import sys
import json
import requests
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table

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

def call_mcp_tool(tool_name, **params):
    """
    Call an MCP tool on the server.
    
    Args:
        tool_name: Name of the tool to call
        **params: Parameters to pass to the tool
        
    Returns:
        Tool result
    """
    url = f"http://localhost:8000/tools/{tool_name}"
    response = requests.post(url, json=params)
    
    if response.status_code != 200:
        console.print(f"[bold red]Error calling tool {tool_name}:[/bold red] {response.text}")
        return None
        
    return response.json()

def test_search_by_role():
    """Test the search_by_role tool."""
    console.print("\n[bold blue]Test 1: Search by Role[/bold blue]")
    
    # Call the tool
    results = call_mcp_tool("search_by_role_tool", keywords="software engineer")
    
    # Display results
    if results:
        display_candidates(results, "Software Engineers")
        
    # Return first candidate ID for later tests
    return results[0]["candidate_id"] if results else None

def test_semantic_search():
    """Test the semantic_search_experience tool."""
    console.print("\n[bold blue]Test 2: Semantic Search[/bold blue]")
    
    # Call the tool
    results = call_mcp_tool("semantic_search_experience_tool", query="data analysis")
    
    # Display results
    if results:
        display_candidates(results, "Data Analysis Experience")

def test_skill_search():
    """Test the find_skill_combinations tool."""
    console.print("\n[bold blue]Test 3: Skill Combinations[/bold blue]")
    
    # Call the tool
    results = call_mcp_tool("find_skill_combinations_tool", skills=["Python", "JavaScript"])
    
    # Display results
    if results:
        display_candidates(results, "Candidates with Python OR JavaScript")

def test_education_search():
    """Test the search_by_education tool."""
    console.print("\n[bold blue]Test 4: Education Search[/bold blue]")
    
    # Call the tool
    results = call_mcp_tool("search_by_education_tool", degree="Computer Science")
    
    # Display results
    if results:
        display_candidates(results, "Computer Science Graduates")

def test_candidate_details(candidate_id):
    """Test the get_candidate_details tool."""
    console.print("\n[bold blue]Test 5: Candidate Details[/bold blue]")
    
    if not candidate_id:
        console.print("[bold red]No candidate ID available for testing[/bold red]")
        return
    
    # Call the tool
    details = call_mcp_tool("get_candidate_details_tool", candidate_id=candidate_id)
    
    if not details:
        return
        
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
    console.print("[bold]HR Intelligence MCP Client Test[/bold]")
    console.print("This script tests the MCP server by calling its tools.")
    
    try:
        # Run tests
        candidate_id = test_search_by_role()
        test_semantic_search()
        test_skill_search()
        test_education_search()
        test_candidate_details(candidate_id)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())