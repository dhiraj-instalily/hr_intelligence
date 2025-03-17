# HR Intelligence Database Module

This module provides a hybrid database solution for storing and searching resume data, combining the strengths of structured data storage with vector-based semantic search.

## Architecture

The database module uses a hybrid approach with two main components:

1. **DuckDB** - A lightweight, embedded SQL database for structured data storage
2. **ChromaDB** - A vector database for semantic search capabilities

This hybrid approach allows for both precise structured queries and fuzzy/semantic searches, providing a powerful and flexible search experience.

## Components

### Schema

The `schema.py` file defines the data models using Pydantic:

- `Candidate` - Main model for candidate information
- `ContactInfo` - Contact information for a candidate
- `Education` - Education information for a candidate
- `WorkExperience` - Work experience information for a candidate
- `SearchQuery` - Search query parameters
- `SearchResult` - Search result with candidate and score

### DuckDB Handler

The `duckdb_handler.py` file provides a handler for DuckDB operations:

- Structured data storage with JSON columns
- Fuzzy search using string similarity functions
- Normalized fields for better matching (e.g., company names)
- Indexing for faster queries

### ChromaDB Handler

The `chroma_handler.py` file provides a handler for ChromaDB operations:

- Vector storage for semantic search
- Embedding generation using Sentence Transformers
- Metadata filtering for hybrid queries
- Optimized text representation for better semantic matching

### Hybrid Search

The `hybrid_search.py` file combines both handlers for powerful search capabilities:

- Weighted scoring combining semantic and fuzzy search results
- Unified interface for searching across both databases
- Configurable weights for different search components
- Detailed match information for understanding search results

## Usage

### Populating the Database

Use the `populate_hybrid_db.py` script to populate the database with resume data:

```bash
python scripts/populate_hybrid_db.py --resumes-dir data/llm_processed_resumes
```

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
```

### Programmatic Usage

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

## Performance Considerations

- The hybrid database is optimized for small to medium datasets (hundreds to thousands of resumes)
- For larger datasets, consider using a more scalable solution like PostgreSQL with pgvector
- The embedding model (`all-MiniLM-L6-v2`) is a good balance of performance and accuracy for local use
- For production use with larger datasets, consider using a more powerful embedding model

## Future Improvements

- Add support for more advanced filtering (e.g., experience years, education level)
- Implement caching for frequently used queries
- Add support for document-level relevance feedback
- Implement more sophisticated scoring algorithms
- Add support for multi-modal search (text + image)
