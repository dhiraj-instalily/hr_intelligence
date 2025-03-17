"""
PDF Parser module for extracting text from PDF files using LlamaParse.
"""

import os
import logging
import nest_asyncio
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Import LlamaParse
from llama_parse import LlamaParse

from ..utils.logger import get_logger

# Apply nest_asyncio to allow async code in synchronous contexts
nest_asyncio.apply()

logger = get_logger(__name__)

class PDFParser:
    """Class for extracting text from PDF files using LlamaParse."""

    def __init__(self, config: Dict):
        """
        Initialize the PDF parser with configuration.

        Args:
            config: Configuration dictionary with PDF parsing settings
        """
        self.config = config
        self.api_key = os.environ.get("LLAMA_CLOUD_API_KEY", config.get("llama_cloud_api_key", ""))
        self.result_type = config.get("result_type", "markdown")
        self.num_workers = config.get("num_workers", 4)
        self.language = config.get("language", "en")
        self.verbose = config.get("verbose", True)

        # Initialize LlamaParse
        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type=self.result_type,
            num_workers=self.num_workers,
            verbose=self.verbose,
            language=self.language
        )

        logger.info(f"Initialized LlamaParse PDF parser with result_type={self.result_type}")

    def extract_text(self, pdf_path: Union[str, Path]) -> str:
        """
        Extract text from a PDF file using LlamaParse.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text as a string
        """
        pdf_path = Path(pdf_path)
        logger.info(f"Extracting text from {pdf_path} using LlamaParse")

        try:
            # Parse the document using LlamaParse
            parsed_documents = self.parser.load_data(str(pdf_path))

            if not parsed_documents:
                logger.warning(f"No content extracted from {pdf_path}")
                return ""

            # Combine all document texts if multiple are returned
            combined_text = "\n\n".join(doc.text for doc in parsed_documents)
            logger.info(f"Successfully extracted {len(combined_text)} characters from {pdf_path}")

            return combined_text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise

    async def extract_text_async(self, pdf_path: Union[str, Path]) -> str:
        """
        Extract text from a PDF file asynchronously using LlamaParse.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text as a string
        """
        pdf_path = Path(pdf_path)
        logger.info(f"Asynchronously extracting text from {pdf_path} using LlamaParse")

        try:
            # Parse the document using LlamaParse asynchronously
            parsed_documents = await self.parser.aload_data(str(pdf_path))

            if not parsed_documents:
                logger.warning(f"No content extracted from {pdf_path}")
                return ""

            # Combine all document texts if multiple are returned
            combined_text = "\n\n".join(doc.text for doc in parsed_documents)
            logger.info(f"Successfully extracted {len(combined_text)} characters from {pdf_path}")

            return combined_text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise

    def batch_process(self, pdf_dir: Union[str, Path], output_dir: Union[str, Path]) -> List[Path]:
        """
        Process all PDFs in a directory and save extracted text.

        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory to save extracted text files

        Returns:
            List of paths to the created text files
        """
        pdf_dir = Path(pdf_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        # Get all PDF files
        pdf_files = list(pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {pdf_dir}")

        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return []

        # Process all PDFs in batch
        try:
            # Convert Path objects to strings
            pdf_paths = [str(pdf) for pdf in pdf_files]

            # Parse all documents in batch
            parsed_documents = self.parser.load_data(pdf_paths)

            # Group documents by their source file
            documents_by_file = {}
            for doc in parsed_documents:
                source = doc.metadata.get('file_path', '')
                if source not in documents_by_file:
                    documents_by_file[source] = []
                documents_by_file[source].append(doc)

            # Save extracted text for each file
            output_files = []
            for pdf_file in pdf_files:
                source = str(pdf_file)
                if source in documents_by_file:
                    # Combine all document texts for this file
                    combined_text = "\n\n".join(doc.text for doc in documents_by_file[source])

                    # Save to output file
                    output_file = output_dir / f"{pdf_file.stem}.txt"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(combined_text)

                    output_files.append(output_file)
                    logger.info(f"Saved extracted text to {output_file}")
                else:
                    logger.warning(f"No content extracted from {pdf_file}")

            return output_files
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            raise

    async def batch_process_async(self, pdf_dir: Union[str, Path], output_dir: Union[str, Path]) -> List[Path]:
        """
        Process all PDFs in a directory asynchronously and save extracted text.

        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory to save extracted text files

        Returns:
            List of paths to the created text files
        """
        pdf_dir = Path(pdf_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        # Get all PDF files
        pdf_files = list(pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {pdf_dir}")

        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return []

        # Process all PDFs in batch asynchronously
        try:
            # Convert Path objects to strings
            pdf_paths = [str(pdf) for pdf in pdf_files]

            # Parse all documents in batch asynchronously
            parsed_documents = await self.parser.aload_data(pdf_paths)

            # Group documents by their source file
            documents_by_file = {}
            for doc in parsed_documents:
                source = doc.metadata.get('file_path', '')
                if source not in documents_by_file:
                    documents_by_file[source] = []
                documents_by_file[source].append(doc)

            # Save extracted text for each file
            output_files = []
            for pdf_file in pdf_files:
                source = str(pdf_file)
                if source in documents_by_file:
                    # Combine all document texts for this file
                    combined_text = "\n\n".join(doc.text for doc in documents_by_file[source])

                    # Save to output file
                    output_file = output_dir / f"{pdf_file.stem}.txt"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(combined_text)

                    output_files.append(output_file)
                    logger.info(f"Saved extracted text to {output_file}")
                else:
                    logger.warning(f"No content extracted from {pdf_file}")

            return output_files
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            raise
