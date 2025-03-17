#!/bin/bash
# Script to set up the database and make the scripts executable

# Make scripts executable
chmod +x scripts/populate_hybrid_db.py
chmod +x scripts/search_resumes.py

# Create necessary directories
mkdir -p data/hr_database
mkdir -p data/chroma_db

# Install dependencies
pip install -r requirements.txt

# Populate the database
echo "Populating the database with resume data..."
python scripts/populate_hybrid_db.py --resumes-dir data/llm_processed_resumes

# Test the search functionality
echo "Testing search functionality..."
python scripts/search_resumes.py --query "software engineering" --limit 5

echo "Database setup complete!"
echo "You can now search for resumes using the search_resumes.py script."
echo "Example: python scripts/search_resumes.py --query \"machine learning\" --skills Python --verbose"