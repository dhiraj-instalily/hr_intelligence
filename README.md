# HR Intelligence

A system for extracting, processing, and querying HR documents using LLMs.

## Overview

HR Intelligence is a tool that helps HR professionals and recruiters extract structured data from unstructured HR documents such as resumes, job descriptions, and performance reviews. It uses LLMs to understand and extract relevant information, stores it in a structured database, and provides a powerful query interface.

## Features

- **Advanced PDF Processing**: Extract text and tables from PDF documents using LlamaParse, with superior table extraction capabilities
- **LLM-based Extraction**: Use GPT-4o to extract structured data from text with high accuracy
- **Function Calling**: Leverage OpenAI's function calling for reliable structured output
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
- ✅ Implemented GPT-4o-based schema extraction for more accurate resume parsing
- ✅ Created an end-to-end pipeline script for the entire extraction process
- ✅ Integrated OpenAI's function calling for reliable structured data extraction
- ✅ Fixed resume extraction to capture complete resume text for each candidate
- ✅ Added preview mode to LLM schema extraction for debugging
- ✅ Added ability to process specific resume files for targeted debugging
- ✅ Improved handling of applicant tables and special cases in resume extraction

### Next Steps

- [ ] Implement database storage for extracted data
- [ ] Develop the query interface for natural language queries
- [ ] Add more test cases and improve error handling
- [ ] Enhance documentation and add usage examples
- [x] Verify individual resume extraction with name-to-text mapping
- [x] Update GPT-4o implementation to use structured output instead of function calling
- [x] Fix resume extraction issues with non-candidate names and name variations

## Debugging Tools

The HR Intelligence system includes several debugging tools to help ensure the quality of extracted data:

### Debug Flag for Resume Extraction

The `--debug` flag with `extract_resumes.py` provides detailed output to verify extraction quality:

```bash
python scripts/extract_resumes.py --input-file data/processed_text/Sales\ Engineer\ AI\ Growth.txt --output-dir data/extracted_resumes --clean --debug
```

This flag:

- Prints the first 10 lines of each extracted resume
- Shows which candidates were successfully extracted
- Helps identify any candidates that couldn't be found
- Verifies that complete resume text is being captured

### Preview Flag for LLM Schema Extraction

The `--preview` flag with `llm_schema_extraction.py` allows you to check what's being sent to the LLM before making API calls:

```bash
python scripts/llm_schema_extraction.py --input-dir data/extracted_resumes --output-dir data/llm_processed_resumes --preview --max-previews 2
```

This flag:

- Shows what would be sent to the LLM without making actual API calls
- Displays both the system message (with schema) and user message (with resume text)
- Helps verify the quality of the text being sent to the LLM
- Use `--max-previews` to control how many previews are shown

### Processing Specific Resume Files

If you need to process a specific resume file (e.g., after fixing extraction issues):

```bash
python scripts/llm_schema_extraction.py --input-dir data/extracted_resumes --output-dir data/llm_processed_resumes --specific-file "Candidate_Name.json"
```

This option:

- Processes only the specified file instead of all files in the directory
- Useful for fixing individual problematic resumes
- Saves time and API calls when debugging specific issues

### Troubleshooting Common Issues

If you encounter issues with the extraction or processing:

1. **Missing or Incorrect Resume Content**:

   - Check the extracted resume in `data/extracted_resumes/Candidate_Name.json`
   - Look at the `raw_text` field to see what was extracted
   - If needed, manually create or fix the JSON file
   - Use the `--specific-file` flag to process just that candidate's resume

2. **Applicant Table Issues**:

   - The extraction script has been improved to handle cases where a candidate's information appears in an applicant table
   - Add name variations to the `name_variations` dictionary in `extract_resumes.py` if needed

3. **LLM Processing Issues**:
   - Use the `--preview` flag to check what's being sent to the LLM
   - Verify that the raw text contains the complete resume information

For more detailed debugging instructions, see the `instruction.txt` file.

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

## GPT-4o Integration

This project uses OpenAI's GPT-4o model for structured data extraction from resume text. The implementation leverages structured output to ensure reliable and consistent structured output.

### GPT-4o Features

- **High Accuracy**: Extracts information with superior accuracy compared to other models
- **Structured Output**: Uses OpenAI's structured output feature for reliable JSON responses
- **Schema Validation**: Extracted data is validated against predefined schemas
- **Consistent Format**: Ensures data is extracted in a consistent format for database storage

### GPT-4o Setup

To use GPT-4o, you need to:

1. Get an API key from [OpenAI](https://platform.openai.com)
2. Set the API key in your environment variables:
   ```
   export OPENAI_API_KEY="sk-your-api-key"
   ```
   Or add it to your `.env` file:
   ```
   OPENAI_API_KEY=sk-your-api-key
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

# Set up your API keys
echo "LLAMA_CLOUD_API_KEY=your-llama-api-key-here" >> .env
echo "OPENAI_API_KEY=your-openai-api-key-here" >> .env
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
3. Process resumes with GPT-4o for accurate schema extraction
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
python scripts/extract_resumes.py --input-file data/processed_text/Sales\ Engineer\ AI\ Growth.txt --output-dir data/extracted_resumes --clean --debug
```

The `--clean` flag will remove all existing JSON files in the output directory before extraction, ensuring clean results.
The `--debug` flag will print the first 10 lines of each extracted resume to verify extraction quality.

#### Verify Resume Extraction

To verify that individual resumes are extracted correctly:

```bash
python scripts/verify_resume_extraction.py --input-file data/processed_text/Sales\ Engineer\ AI\ Growth.txt --output-file data/verification/name_to_text_map.json
```

This creates a mapping from candidate names to their raw resume text, which can be manually inspected to ensure proper extraction.

**Improvements to Resume Extraction:**

- ✅ Fixed extraction of non-candidate headings (like "COMMUNITY_INVOLVEMENT", "PROFESSIONAL_EXPERIENCE")
- ✅ Added support for candidates with name variations (e.g., "Nimeesh Bagwe" vs "NIMEESH NILESH BAGWE")
- ✅ Implemented special case handling for hard-to-find candidates
- ✅ Added email-based search for candidates whose names can't be found in headings
- ✅ Improved heading pattern matching to handle different formatting styles
- ✅ Enhanced resume extraction to capture the full text between candidate headings
- ✅ Added debug output to verify extraction quality

**Known Issues:**

- Some extracted resumes may contain limited information if the original text doesn't follow standard formatting
- The extraction process relies on consistent heading patterns in the document

#### Process Resumes with GPT-4o

```bash
# Preview mode (doesn't call the API, just shows what would be sent)
python scripts/llm_schema_extraction.py --input-dir data/extracted_resumes --output-dir data/llm_processed_resumes --preview --max-previews 2

# Full processing
python scripts/llm_schema_extraction.py --input-dir data/extracted_resumes --output-dir data/llm_processed_resumes
```

The `--preview` flag allows you to see what would be sent to the LLM without making actual API calls, which is useful for debugging.

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
│   └── llm_processed_resumes/ # GPT-4o-processed resume JSON files
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
│   ├── llm_schema_extraction.py # GPT-4o-based schema extraction
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

3. Process resumes with GPT-4o for accurate schema extraction:

   ```bash
   python scripts/llm_schema_extraction.py
   ```

4. Insert the processed resumes into the database:

   ```bash
   python scripts/populate_database.py
   ```

## Function Calling for Structured Output

The system uses OpenAI's function calling feature to ensure reliable structured output from GPT-4o. This approach:

1. Defines a function schema that matches our Pydantic models
2. Instructs GPT-4o to extract information according to this schema
3. Returns structured JSON that can be directly validated against our models
4. Ensures consistent output format for database storage

Example function definition:

```python
functions = [
    {
        "name": "extract_resume_data",
        "description": "Extract structured information from a resume text",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate_name": {"type": "string"},
                "contact_info": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        # Additional properties...
                    }
                },
                # Additional properties...
            },
            "required": ["document_type", "candidate_name", "contact_info"]
        }
    }
]
```

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
