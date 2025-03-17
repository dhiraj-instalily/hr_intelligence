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
│   └── json_data/           # LLM-processed JSON files (schema-compliant)
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
│   └── db_cleanup.py        # Database maintenance
│
├── tests/                   # Unit and integration tests
│   ├── test_ingestion.py
│   └── test_retrieval.py
│
├── .env                     # Environment variables (API keys, DB creds)
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/hr_intelligence.git
   cd hr_intelligence
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## Usage

### Processing PDF Documents

To process a single PDF document:

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

To batch process multiple PDF documents:

```bash
python scripts/batch_ingest.py --input-dir data/raw_pdfs --output-dir data/processed_text --json-dir data/json_data
```

### Querying the Database

```python
from src.retrieval.database_connector import DatabaseConnector
from src.retrieval.query_tools import QueryTools
from src.utils.helpers import load_config

# Load configuration
config = load_config()

# Initialize components
db = DatabaseConnector(config.get('database', {}))
query_tools = QueryTools(db, config.get('llm', {}))

# Execute a natural language query
results = query_tools.execute_query("Find software engineers with Python experience")

# Print results
for result in results.get('results', []):
    print(f"Candidate: {result['content'].get('candidate_name')}")
    print(f"Skills: {', '.join(result['content'].get('skills', []))}")
    print("---")
```

## Testing

Run the tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=src tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
