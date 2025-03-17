# HR Intelligence

A system for extracting, processing, and querying HR documents using LLMs.

## Overview

HR Intelligence is a tool that helps HR professionals and recruiters extract structured data from unstructured HR documents such as resumes, job descriptions, and performance reviews. It uses LLMs to understand and extract relevant information, stores it in a structured database, and provides a powerful query interface.

## Features

- **Advanced PDF Processing**: Extract text and tables from PDF documents using LlamaParse, with superior table extraction capabilities
- **LLM-based Extraction**: Use large language models to extract structured data from text
- **Schema Validation**: Validate extracted data against predefined schemas
- **Database Storage**: Store extracted data in a structured database
- **Natural Language Queries**: Query the database using natural language
- **Caching**: Cache query results for improved performance

## Project Status

### What's Been Done

- ✅ Project structure and configuration set up
- ✅ LlamaParse integration for advanced PDF parsing
- ✅ PDF parsing functionality implemented and tested
- ✅ Successfully parsed sample resume data ("Sales Engineer AI Growth.pdf")
- ✅ Basic data extraction and JSON output implemented
- ✅ GitHub repository established at [https://github.com/dhiraj-instalily/hr_intelligence](https://github.com/dhiraj-instalily/hr_intelligence)
- ✅ Added scripts to extract individual resumes from a single PDF and populate the database
- ✅ Improved resume extraction by identifying candidates from tables
- ✅ Implemented LLM-based schema extraction for more accurate resume parsing
- ✅ Created an end-to-end pipeline script for the entire extraction process

### Next Steps

- [ ] Implement database storage for extracted data
- [ ] Develop the query interface for natural language queries
- [ ] Add more test cases and improve error handling
- [ ] Enhance documentation and add usage examples

## LlamaParse Integration

This project uses [LlamaParse](https://docs.llamaindex.ai/en/v0.10.34/module_guides/loading/connector/llama_parse/) for advanced PDF parsing. LlamaParse is a proprietary parsing service designed to handle the complexities of PDFs and other document types, with industry-leading table extraction capabilities.

### LlamaParse Features

- **Superior Table Extraction**: Extracts tables from PDFs with high accuracy
- **Markdown Output**: Converts PDFs to well-structured markdown format
- **Batch Processing**: Efficiently processes multiple documents
- **Asynchronous API**: Supports both synchronous and asynchronous processing

### LlamaParse Setup

To use LlamaParse, you need to:

1. Get an API key from [LlamaCloud](https://cloud.llamaindex.ai)
2. Set the API key in your environment variables:
   ```
   export LLAMA_CLOUD_API_KEY="llx-your-api-key"
   ```
   Or add it to your `.env` file:
   ```
   LLAMA_CLOUD_API_KEY=llx-your-api-key
   ```

## Quick Start Guide

### 1. Clone the Repository

```bash
git clone https://github.com/dhiraj-instalily/hr_intelligence.git
cd hr_intelligence
```

### 2. Set Up Environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your LlamaCloud API key
echo "LLAMA_CLOUD_API_KEY=your-api-key-here" >> .env
```

### 3. Run the Complete Pipeline

You can run the entire extraction and processing pipeline with a single script:

```bash
# Make the script executable
chmod +x scripts/run_resume_extraction_pipeline.sh

# Run the pipeline
./scripts/run_resume_extraction_pipeline.sh
```

This script will:

1. Parse the PDF (if not already done)
2. Extract individual resumes
3. Process resumes with LLM for accurate schema extraction
4. Populate the database (if the script exists)

### 4. Run Individual Steps

Alternatively, you can run each step individually:

#### Parse a PDF

```bash
# Place your PDF in the raw_pdfs directory
mkdir -p data/raw_pdfs
cp your-document.pdf data/raw_pdfs/

# Run the parsing script
python parse_pdf.py
```

#### Extract Individual Resumes

```bash
python scripts/extract_resumes.py --input-file data/processed_text/Sales\ Engineer\ AI\ Growth.txt --output-dir data/extracted_resumes
```

#### Process Resumes with LLM

```bash
python scripts/llm_schema_extraction.py --input-dir data/extracted_resumes --output-dir data/llm_processed_resumes
```

#### Populate the Database

```bash
python scripts/populate_database.py --resumes-dir data/llm_processed_resumes --config config/config.yaml
```

## Project Structure

```
hr_intelligence/
│
├── config/                   # Configuration files
│   ├── config.yaml          # Main configuration (DB paths, model names)
│   └── prompts/             # LLM prompt templates
│       ├── extraction_prompt.txt
│       └── query_rewrite_prompt.txt
│
├── data/                    # Data storage
│   ├── raw_pdfs/            # Original PDF files
│   ├── processed_text/      # Extracted text from PDFs
│   ├── json_data/           # JSON files from initial parsing
│   ├── extracted_resumes/   # Individual resume JSON files
│   └── llm_processed_resumes/ # LLM-processed resume JSON files
│
├── src/
│   ├── ingestion/           # Data processing pipeline
│   │   ├── pdf_parser.py    # PDF → text conversion using LlamaParse
│   │   ├── data_extractor.py# LLM-based schema extraction
│   │   └── database_handler.py  # DB population
│   │
│   ├── retrieval/           # Query handling
│   │   ├── query_tools.py   # Tool definitions for LLM agent
│   │   ├── database_connector.py # DB query logic
│   │   ├── schema.py        # Pydantic models for data validation
│   │   └── cache.py         # Query caching system
│   │
│   └── utils/               # Shared utilities
│       ├── logger.py        # Logging configuration
│       └── helpers.py       # Common helper functions
│
├── scripts/                 # Utility scripts
│   ├── batch_ingest.py      # Bulk PDF processing
│   ├── extract_resumes.py   # Extract individual resumes from processed text
│   ├── llm_schema_extraction.py # LLM-based schema extraction
│   ├── populate_database.py # Insert extracted resumes into database
│   ├── run_resume_extraction_pipeline.sh # End-to-end pipeline script
│   └── db_cleanup.py        # Database maintenance
│
├── tests/                   # Unit and integration tests
│   ├── test_ingestion.py
│   └── test_retrieval.py
│
├── parse_pdf.py             # Standalone script for parsing a single PDF
├── run_ingest.sh            # Helper script for running batch ingest with API key
├── .env                     # Environment variables (API keys, DB creds)
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

## Advanced Usage

### Processing PDF Documents

To process a single PDF document programmatically:

```python
from src.ingestion.pdf_parser import PDFParser
from src.ingestion.data_extractor import DataExtractor
from src.ingestion.database_handler import DatabaseHandler
from src.utils.helpers import load_config

# Load configuration
config = load_config()

# Initialize components
pdf_parser = PDFParser(config.get('pdf', {}))
data_extractor = DataExtractor(config.get('llm', {}))
db_handler = DatabaseHandler(config.get('database', {}))

# Process a PDF file
pdf_path = "data/raw_pdfs/resume.pdf"
text = pdf_parser.extract_text(pdf_path)
extracted_data = data_extractor.extract_data(text)
db_handler.insert_document(extracted_data.get('document_type'), pdf_path, extracted_data)
```

### Asynchronous Processing

For improved performance with multiple documents, use the asynchronous API:

```bash
python scripts/batch_ingest.py --input-dir data/raw_pdfs --output-dir data/processed_text --json-dir data/json_data --async
```

### Handling Multi-Resume PDFs

Our improved workflow for processing collections of resumes:

1. Parse the PDF using LlamaParse:

   ```bash
   python parse_pdf.py
   ```

2. Extract individual resumes by identifying candidates from tables:

   ```bash
   python scripts/extract_resumes.py
   ```

3. Process resumes with LLM for accurate schema extraction:

   ```bash
   python scripts/llm_schema_extraction.py
   ```

4. Insert the processed resumes into the database:
   ```bash
   python scripts/populate_database.py
   ```

Or simply run the entire pipeline with a single command:

```bash
./scripts/run_resume_extraction_pipeline.sh
```

This workflow allows you to process collections of resumes efficiently and store them in a structured format for querying.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

To contribute to this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
