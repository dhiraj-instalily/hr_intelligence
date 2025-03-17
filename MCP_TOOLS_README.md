# HR Intelligence MCP Tools

This document provides detailed information about the Model Context Protocol (MCP) tools implemented for the HR Intelligence database.

## Overview

The HR Intelligence MCP tools provide a structured way for AI assistants to interact with the HR database. These tools allow for searching candidates by various criteria, performing semantic searches, and retrieving detailed candidate information.

## Components

- **MCP Server** (`mcp_server.py`): Exposes the HR database functionality as tools for AI assistants
- **MCP Client** (`mcp_client.py`): Example client for testing the MCP tools
- **Fixed HR Tools** (`fixed_hr_tools.py`): Core functionality for database interaction

## Available Tools

### 1. Search by Role Tool

Performs a fuzzy search for candidates based on roles/responsibilities with an optional company filter.

**Function Name:** `search_by_role_tool`

**Parameters:**
- `keywords` (str): Keywords to search for in roles and responsibilities
- `company` (str, optional): Company name to filter by

**Returns:**
- List of candidates matching the search criteria, including:
  - Candidate ID
  - Name
  - Matching work experience details
  - Relevance score

**Example Usage:**
```python
results = search_by_role_tool(keywords="software engineer", company="Google")
```

### 2. Semantic Search Experience Tool

Conducts deep semantic searches across all work experiences using vector embeddings.

**Function Name:** `semantic_search_experience_tool`

**Parameters:**
- `query` (str): Semantic query to search for in work experiences

**Returns:**
- List of candidates with semantically matching experiences, including:
  - Candidate ID
  - Name
  - Matching work experience details
  - Semantic similarity score

**Example Usage:**
```python
results = semantic_search_experience_tool(query="developed scalable cloud infrastructure")
```

### 3. Find Skill Combinations Tool

Finds candidates based on specified skills, with options for AND/OR logic.

**Function Name:** `find_skill_combinations_tool`

**Parameters:**
- `skills` (List[str]): List of skills to search for
- `match_all` (bool, optional): If True, candidates must have ALL skills; if False, ANY skill is sufficient (default: False)

**Returns:**
- List of candidates matching the skill criteria, including:
  - Candidate ID
  - Name
  - Matching skills
  - Skill match count

**Example Usage:**
```python
results = find_skill_combinations_tool(skills=["Python", "React", "AWS"], match_all=True)
```

### 4. Get Candidate Details Tool

Retrieves detailed information about a specific candidate by their ID.

**Function Name:** `get_candidate_details_tool`

**Parameters:**
- `candidate_id` (str): Unique identifier for the candidate

**Returns:**
- Complete candidate profile with all available information:
  - Personal details
  - Work experiences
  - Education history
  - Skills
  - Certifications

**Example Usage:**
```python
candidate = get_candidate_details_tool(candidate_id="12345")
```

### 5. Search by Education Tool

Searches for candidates based on their educational background.

**Function Name:** `search_by_education_tool`

**Parameters:**
- `institution` (str, optional): Educational institution name
- `degree` (str, optional): Degree or field of study

**Returns:**
- List of candidates matching the education criteria, including:
  - Candidate ID
  - Name
  - Matching education details

**Example Usage:**
```python
results = search_by_education_tool(institution="Stanford", degree="Computer Science")
```

## Running the MCP Server

To start the MCP server:

```bash
python mcp_server.py
```

The server will start on `localhost:8000` by default.

## Testing with the MCP Client

To test the MCP tools using the provided client:

```bash
python mcp_client.py
```

The client will run a series of tests for each tool and display the results.

## Implementation Details

### Database Connection

The MCP tools connect directly to the HR database using:
- **DuckDB** for structured data queries
- **ChromaDB** for semantic searches

### Result Processing

The tools process database results to ensure they are:
- JSON-serializable
- Properly formatted for API responses
- Consistent across different query types

### Error Handling

The tools include robust error handling for:
- Database connection issues
- Invalid query parameters
- Missing data
- Serialization errors

## Integration with AI Assistants

AI assistants that support the Model Context Protocol can use these tools by:

1. Connecting to the MCP server
2. Discovering available tools
3. Calling the tools with appropriate parameters
4. Processing the returned results

## Troubleshooting

### Server Won't Start

If the MCP server fails to start:
- Check that all dependencies are installed
- Verify that the database files exist at the expected locations
- Check for port conflicts (default is 8000)

### Tool Execution Errors

If tools fail to execute:
- Check the server logs for error messages
- Verify that the database is properly populated
- Ensure the parameters are correctly formatted

### Client Connection Issues

If the client fails to connect:
- Verify that the server is running
- Check that the client is using the correct URL
- Ensure there are no network issues or firewalls blocking the connection

## Future Improvements

Planned improvements for the MCP tools include:
- Authentication and authorization
- Rate limiting
- More advanced search capabilities
- Tools for database administration
- Web UI for tool testing and demonstration