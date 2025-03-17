#!/bin/bash
# Script to run the entire resume extraction and LLM processing pipeline

# Set the base directory
BASE_DIR=$(dirname "$(dirname "$(realpath "$0")")")
cd "$BASE_DIR" || exit 1

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable not set"
    echo "Please set it in the .env file or export it before running this script"
    exit 1
fi

# Create necessary directories
mkdir -p data/processed_text
mkdir -p data/extracted_resumes
mkdir -p data/llm_processed_resumes

# Step 1: Parse the PDF (if not already done)
if [ ! -f "data/processed_text/Sales Engineer AI Growth.txt" ]; then
    echo "Step 1: Parsing PDF..."
    python parse_pdf.py
else
    echo "Step 1: PDF already parsed, skipping"
fi

# Step 2: Extract individual resumes
echo "Step 2: Extracting individual resumes..."
python scripts/extract_resumes.py --input-file "data/processed_text/Sales Engineer AI Growth.txt" --output-dir "data/extracted_resumes" --clean

# Step 3: Process resumes with GPT-4o
echo "Step 3: Processing resumes with GPT-4o..."
python scripts/llm_schema_extraction.py --input-dir "data/extracted_resumes" --output-dir "data/llm_processed_resumes"

# Step 4: Populate the database (if script exists)
if [ -f "scripts/populate_database.py" ]; then
    echo "Step 4: Populating database..."
    python scripts/populate_database.py --resumes-dir "data/llm_processed_resumes" --config "config/config.yaml"
else
    echo "Step 4: Database population script not found, skipping"
fi

echo "Pipeline completed successfully!"
