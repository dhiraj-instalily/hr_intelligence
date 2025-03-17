#!/usr/bin/env python3
"""
Script to parse a PDF file using LlamaParse and save the results.
"""

import os
import sys
from pathlib import Path
import nest_asyncio
from llama_parse import LlamaParse

# Apply nest_asyncio to allow async code in synchronous contexts
nest_asyncio.apply()

# Set up API key
api_key = "llx-5xUPcHiqdUeb85r1YPJ8miRNHQMvYLpOVJZrWv1J07Pqfdc2"
os.environ["LLAMA_CLOUD_API_KEY"] = api_key

# Initialize LlamaParse
parser = LlamaParse(
    api_key=api_key,
    result_type="markdown",
    num_workers=4,
    verbose=True,
    language="en"
)

# Define paths
pdf_path = "data/raw_pdfs/Sales Engineer AI Growth.pdf"
output_text_path = "data/processed_text/Sales Engineer AI Growth.txt"
output_json_path = "data/json_data/Sales Engineer AI Growth.json"

# Parse the document
print(f"Parsing {pdf_path}...")
documents = parser.load_data(pdf_path)

if documents:
    print(f"Successfully parsed {pdf_path}")
    
    # Save the extracted text
    combined_text = "\n\n".join(doc.text for doc in documents)
    
    # Create output directories if they don't exist
    Path(output_text_path).parent.mkdir(exist_ok=True, parents=True)
    Path(output_json_path).parent.mkdir(exist_ok=True, parents=True)
    
    # Save text output
    with open(output_text_path, 'w', encoding='utf-8') as f:
        f.write(combined_text)
    print(f"Saved extracted text to {output_text_path}")
    
    # Save JSON output (simplified version)
    import json
    json_data = {
        "document_type": "job_description",
        "job_title": "Sales Engineer AI Growth",
        "content": combined_text,
        "file_name": Path(pdf_path).name
    }
    
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    print(f"Saved JSON data to {output_json_path}")
    
    print("Processing complete!")
else:
    print(f"Failed to extract content from {pdf_path}")