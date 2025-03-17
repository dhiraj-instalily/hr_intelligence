#!/usr/bin/env python3
"""
Batch Ingest Script for processing multiple PDF files.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.pdf_parser import PDFParser
from src.ingestion.data_extractor import DataExtractor
from src.ingestion.database_handler import DatabaseHandler
from src.utils.logger import get_logger, setup_file_logging
from src.utils.helpers import load_config, ensure_dir

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Batch process PDF files for HR intelligence")
    
    parser.add_argument(
        "--input-dir", 
        type=str, 
        default="data/raw_pdfs",
        help="Directory containing PDF files to process"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/processed_text",
        help="Directory to save extracted text files"
    )
    
    parser.add_argument(
        "--json-dir", 
        type=str, 
        default="data/json_data",
        help="Directory to save extracted JSON files"
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/config.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--log-dir", 
        type=str, 
        default="logs",
        help="Directory to save log files"
    )
    
    parser.add_argument(
        "--skip-existing", 
        action="store_true",
        help="Skip files that have already been processed"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without actually processing files"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Set up logging
    setup_file_logging(args.log_dir)
    logger.info("Starting batch ingest process")
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.error("Failed to load configuration")
        return 1
    
    # Initialize components
    pdf_parser = PDFParser(config.get('pdf', {}))
    data_extractor = DataExtractor(config.get('llm', {}))
    db_handler = DatabaseHandler(config.get('database', {}))
    
    # Ensure directories exist
    input_dir = ensure_dir(args.input_dir)
    output_dir = ensure_dir(args.output_dir)
    json_dir = ensure_dir(args.json_dir)
    
    # Get list of PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {input_dir}")
    
    if args.dry_run:
        logger.info("Dry run mode - no files will be processed")
        for pdf_file in pdf_files:
            logger.info(f"Would process: {pdf_file}")
        return 0
    
    # Process each PDF file
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for pdf_file in pdf_files:
        text_file = output_dir / f"{pdf_file.stem}.txt"
        json_file = json_dir / f"{pdf_file.stem}.json"
        
        # Skip if output files already exist and --skip-existing is set
        if args.skip_existing and text_file.exists() and json_file.exists():
            logger.info(f"Skipping {pdf_file.name} - already processed")
            skipped_count += 1
            continue
        
        try:
            # Extract text from PDF
            logger.info(f"Processing {pdf_file.name}")
            text = pdf_parser.extract_text(pdf_file)
            
            # Save extracted text
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Saved extracted text to {text_file}")
            
            # Extract structured data
            extracted_data = data_extractor.extract_data(text)
            
            # Save extracted data as JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(extracted_data, f, indent=2)
            logger.info(f"Saved extracted data to {json_file}")
            
            # Insert into database
            document_type = extracted_data.get('document_type', 'unknown')
            db_handler.insert_document(document_type, pdf_file.name, extracted_data)
            logger.info(f"Inserted {document_type} document into database")
            
            processed_count += 1
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {e}")
            error_count += 1
    
    # Log summary
    logger.info(f"Batch processing complete")
    logger.info(f"Processed: {processed_count}")
    logger.info(f"Skipped: {skipped_count}")
    logger.info(f"Errors: {error_count}")
    
    # Close database connection
    db_handler.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())