#!/usr/bin/env python3
"""
Batch Ingest Script for processing multiple PDF files.
"""

import argparse
import os
import sys
import asyncio
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

    parser.add_argument(
        "--async",
        action="store_true",
        dest="use_async",
        help="Use asynchronous processing"
    )

    return parser.parse_args()

async def async_main(args):
    """Asynchronous main entry point for the script."""
    # Set up logging
    setup_file_logging(args.log_dir)
    logger.info("Starting batch ingest process (async mode)")

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

    # Process PDFs in batch using async method
    try:
        output_files = await pdf_parser.batch_process_async(input_dir, output_dir)
        logger.info(f"Processed {len(output_files)} PDF files")

        # Process each extracted text file to extract structured data
        processed_count = 0
        skipped_count = 0
        error_count = 0

        for text_file in output_files:
            json_file = json_dir / f"{text_file.stem}.json"

            # Skip if JSON file already exists and --skip-existing is set
            if args.skip_existing and json_file.exists():
                logger.info(f"Skipping {text_file.name} - already processed")
                skipped_count += 1
                continue

            try:
                # Extract structured data
                extracted_data = data_extractor.process_file(text_file, json_file)

                # Insert into database
                document_type = extracted_data.get('document_type', 'unknown')
                db_handler.insert_document(document_type, text_file.stem + ".pdf", extracted_data)
                logger.info(f"Inserted {document_type} document into database")

                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing {text_file.name}: {e}")
                error_count += 1

        # Log summary
        logger.info(f"Batch processing complete")
        logger.info(f"Processed: {processed_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info(f"Errors: {error_count}")

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        return 1
    finally:
        # Close database connection
        db_handler.close()

    return 0

def main():
    """Main entry point for the script."""
    args = parse_args()

    # Use async processing if requested
    if args.use_async:
        return asyncio.run(async_main(args))

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

    # Process PDFs in batch
    try:
        output_files = pdf_parser.batch_process(input_dir, output_dir)
        logger.info(f"Processed {len(output_files)} PDF files")

        # Process each extracted text file to extract structured data
        processed_count = 0
        skipped_count = 0
        error_count = 0

        for text_file in output_files:
            json_file = json_dir / f"{text_file.stem}.json"

            # Skip if JSON file already exists and --skip-existing is set
            if args.skip_existing and json_file.exists():
                logger.info(f"Skipping {text_file.name} - already processed")
                skipped_count += 1
                continue

            try:
                # Extract structured data
                extracted_data = data_extractor.process_file(text_file, json_file)

                # Insert into database
                document_type = extracted_data.get('document_type', 'unknown')
                db_handler.insert_document(document_type, text_file.stem + ".pdf", extracted_data)
                logger.info(f"Inserted {document_type} document into database")

                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing {text_file.name}: {e}")
                error_count += 1

        # Log summary
        logger.info(f"Batch processing complete")
        logger.info(f"Processed: {processed_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info(f"Errors: {error_count}")

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        return 1
    finally:
        # Close database connection
        db_handler.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
