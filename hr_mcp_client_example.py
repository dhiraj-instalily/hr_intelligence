#!/usr/bin/env python3
"""
Example client for the HR Intelligence MCP Server

This script demonstrates how to use the MCP client to interact with
the HR Intelligence database through the MCP server.

Usage:
    python hr_mcp_client_example.py

Make sure the MCP server is running before executing this script.
"""

import sys
import json
import asyncio
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table

# Import MCP client
from mcp import ClientSession
import requests

# Initialize console for pretty printing
console = Console()

class SimpleHTTPClient:
    """
    A simple HTTP client for MCP servers.
    
    This is a simplified client that uses HTTP requests to call MCP tools.
    In a production environment, you would use the full MCP client with proper
    protocol handling.
    """
    
    def __init__(self, base_url: str):
        """
        Initialize the client with the base URL of the MCP server.
        
        Args:
            base_url: Base URL of the MCP server
        """
        self.base_url = base_url
        
    def __getattr__(self, name: str):
        """
        Dynamically create methods for MCP tools.
        
        Args:
            name: Name of the tool to call
            
        Returns:
            A function that calls the tool
        """
        def call_tool(**kwargs):
            """Call the tool with the given arguments."""
            url = f"{self.base_url}/tools/{name}"
            response = requests.post(url, json=kwargs)
            
            if response.status_code != 200:
                console.print(f"[bold red]Error calling tool {name}: {response.status_code}[/bold red]")
                console.print(response.text)
                return None
                
            return response.json()
            
        return call_tool

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
    
    if candidates and "score" in candidates[0]:
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

def example_role_search(client):
    """Example of searching by role."""
    console.print("\n[bold blue]Example 1: Search by Role[/bold blue]")
    
    # Call the search_by_role tool
    results = client.search_by_role(
        keywords="software engineer",
        company="Google"
    )
    
    # Display results
    display_candidates(results, "Software Engineers at Google")

def example_semantic_search(client):
    """Example of semantic search."""
    console.print("\n[bold blue]Example 2: Semantic Search[/bold blue]")
    
    # Call the semantic_search_experience tool
    results = client.semantic_search_experience(
        query="Experience leading machine learning projects and teams"
    )
    
    # Display results
    display_candidates(results, "ML Leadership Experience")

def example_skill_search(client):
    """Example of searching by skills."""
    console.print("\n[bold blue]Example 3: Skill Combinations[/bold blue]")
    
    # Call the find_skill_combinations tool
    results = client.find_skill_combinations(
        skills=["Python", "Machine Learning", "TensorFlow"],
        match_all=True
    )
    
    # Display results
    display_candidates(results, "Candidates with ALL Required Skills")
    
    # Now try with ANY match
    results = client.find_skill_combinations(
        skills=["Python", "Machine Learning", "TensorFlow"],
        match_all=False
    )
    
    # Display results
    display_candidates(results, "Candidates with ANY Required Skills")

def example_education_search(client):
    """Example of searching by education."""
    console.print("\n[bold blue]Example 4: Education Search[/bold blue]")
    
    # Call the search_by_education tool
    results = client.search_by_education(
        institution="Stanford",
        degree="Computer Science"
    )
    
    # Display results
    display_candidates(results, "Stanford CS Graduates")

def example_candidate_details(client):
    """Example of getting candidate details."""
    console.print("\n[bold blue]Example 5: Candidate Details[/bold blue]")
    
    # First get a candidate ID from a search
    search_results = client.search_by_role(keywords="software engineer")
    
    if not search_results:
        console.print("[bold red]No candidates found to show details[/bold red]")
        return
        
    # Get the first candidate's ID
    candidate_id = search_results[0]["candidate_id"]
    
    # Call the get_candidate_details tool
    details = client.get_candidate_details(candidate_id=candidate_id)
    
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
    """Main entry point for the example client."""
    console.print("[bold]HR Intelligence MCP Client Example[/bold]")
    console.print("This script demonstrates how to use the MCP client to interact with the HR Intelligence database.")
    
    try:
        # Create a simple HTTP client
        client = SimpleHTTPClient("http://localhost:8000")
        
        # Run examples
        example_role_search(client)
        example_semantic_search(client)
        example_skill_search(client)
        example_education_search(client)
        example_candidate_details(client)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        console.print("[yellow]Make sure the MCP server is running on http://localhost:8000[/yellow]")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())