# HR Intelligence Database

This document provides instructions on how to set up and use the HR Intelligence database system.

## Overview

The HR Intelligence database is a hybrid system that combines:

1. **DuckDB** - A lightweight, embedded SQL database for structured data storage
2. **ChromaDB** - A vector database for semantic search capabilities

This hybrid approach allows for both precise structured queries and fuzzy/semantic searches, providing a powerful and flexible search experience.

## Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository (if you haven't already):

   ```bash
   git clone https://github.com/dhiraj-instalily/hr_intelligence.git
   cd hr_intelligence
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the setup script:

   ```bash
   ./scripts/setup_database.sh
   ```

   This script will:

   - Make the necessary scripts executable
   - Create the required directories
   - Install dependencies
   - Populate the database with resume data
   - Test the search functionality

## Usage

### Searching Resumes

Use the `search_resumes.py` script to search for resumes:

```bash
# Semantic search
python scripts/search_resumes.py --query "web development experience with React"

# Skill-based search
python scripts/search_resumes.py --skills Python JavaScript React

# Company-based search
python scripts/search_resumes.py --companies "Google" "Microsoft"

# Role-based search
python scripts/search_resumes.py --roles "Software Engineer" "Data Scientist"

# Education-based search
python scripts/search_resumes.py --education "Stanford" "MIT"

# Combined search
python scripts/search_resumes.py --query "machine learning" --skills Python TensorFlow --companies "Google"

# Verbose output (with match details)
python scripts/search_resumes.py --query "software engineering" --verbose
```

### Populating the Database

If you need to repopulate the database or add new resumes, use the `populate_hybrid_db.py` script:

```bash
python scripts/populate_hybrid_db.py --resumes-dir data/llm_processed_resumes
```

You can also specify custom paths for the databases:

```bash
python scripts/populate_hybrid_db.py --resumes-dir data/llm_processed_resumes --duckdb-path custom/path/database.duckdb --chroma-path custom/path/chroma_db
```

## Database Structure

### DuckDB Tables

- **candidates** - Main table for candidate information
- **work_experience** - Table for work experience information
- **education** - Table for education information
- **skills** - Table for skills information

### ChromaDB Collections

- **candidates** - Collection for candidate embeddings and metadata

## Advanced Usage

### Programmatic Usage

You can use the database programmatically in your Python code:

```python
from src.database.schema import SearchQuery
from src.database.hybrid_search import HybridSearchHandler

# Initialize handler
db_handler = HybridSearchHandler()

# Create search query
query = SearchQuery(
    text="machine learning experience with Python",
    skills=["Python", "TensorFlow"],
    companies=["Google", "Microsoft"],
    limit=5
)

# Perform search
results = db_handler.search(query)

# Process results
for result in results:
    print(f"Candidate: {result.candidate.candidate_name}, Score: {result.score}")
    print(f"Skills: {', '.join(result.candidate.skills[:5])}")
    print("---")

# Close connection
db_handler.close()
```

### Customizing Search Weights

You can customize the weights for different search components:

```python
query = SearchQuery(
    text="machine learning",
    skills=["Python"],
    semantic_weight=0.7,  # Increase weight of semantic search
    fuzzy_weight=0.2,     # Decrease weight of fuzzy search
    exact_weight=0.1      # Keep exact match weight the same
)
```

## Troubleshooting

### Common Issues

1. **Missing dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Permission denied when running scripts**:

   ```bash
   chmod +x scripts/populate_hybrid_db.py
   chmod +x scripts/search_resumes.py
   ```

3. **No results found**:

   - Check that the database has been populated
   - Try a more general query
   - Check that the resume data is in the correct format

4. **Slow search performance**:
   - Reduce the number of results with `--limit`
   - Use more specific search terms
   - Consider using a smaller embedding model

## Additional Resources

- [DuckDB Documentation](https://duckdb.org/docs/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers Documentation](https://www.sbert.net/)
