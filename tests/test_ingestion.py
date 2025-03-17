"""
Tests for the ingestion module.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.pdf_parser import PDFParser
from src.ingestion.data_extractor import DataExtractor
from src.ingestion.database_handler import DatabaseHandler

class TestPDFParser(unittest.TestCase):
    """Tests for the PDFParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'ocr_enabled': True,
            'min_confidence': 0.8
        }
        self.parser = PDFParser(self.config)
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.parser.ocr_enabled, True)
        self.assertEqual(self.parser.min_confidence, 0.8)
    
    def test_extract_text(self):
        """Test text extraction."""
        # Create a mock PDF file
        pdf_path = Path("test.pdf")
        
        # Test extraction
        text = self.parser.extract_text(pdf_path)
        self.assertIsInstance(text, str)
        self.assertIn("Extracted text from test.pdf", text)
    
    def test_batch_process(self):
        """Test batch processing."""
        # Create mock directories
        pdf_dir = Path("pdf_dir")
        output_dir = Path("output_dir")
        
        # Mock the glob method to return a list of PDF files
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = [Path("pdf_dir/test1.pdf"), Path("pdf_dir/test2.pdf")]
            
            # Mock the mkdir method
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                # Mock the open function
                with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
                    # Test batch processing
                    output_files = self.parser.batch_process(pdf_dir, output_dir)
                    
                    # Check that the correct number of files were processed
                    self.assertEqual(len(output_files), 2)
                    
                    # Check that the output directory was created
                    mock_mkdir.assert_called_once_with(exist_ok=True, parents=True)
                    
                    # Check that files were opened for writing
                    self.assertEqual(mock_open.call_count, 2)

class TestDataExtractor(unittest.TestCase):
    """Tests for the DataExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'model_name': 'gpt-4',
            'temperature': 0.1,
            'max_tokens': 1000
        }
        
        # Mock the open function for loading the prompt
        with patch('builtins.open', unittest.mock.mock_open(read_data="Test prompt")) as mock_open:
            self.extractor = DataExtractor(self.config)
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.extractor.model_name, 'gpt-4')
        self.assertEqual(self.extractor.temperature, 0.1)
        self.assertEqual(self.extractor.max_tokens, 1000)
        self.assertEqual(self.extractor.extraction_prompt, "Test prompt")
    
    def test_extract_data(self):
        """Test data extraction."""
        # Test extraction
        data = self.extractor.extract_data("Test text")
        
        # Check that the result is a dictionary
        self.assertIsInstance(data, dict)
        
        # Check that the expected fields are present
        self.assertIn('document_type', data)
        self.assertIn('candidate_name', data)
        self.assertIn('contact_info', data)
        self.assertIn('education', data)
        self.assertIn('work_experience', data)
        self.assertIn('skills', data)
    
    def test_process_file(self):
        """Test file processing."""
        # Mock the open function
        with patch('builtins.open', unittest.mock.mock_open(read_data="Test text")) as mock_open:
            # Test file processing
            data = self.extractor.process_file("test.txt", "test.json")
            
            # Check that the result is a dictionary
            self.assertIsInstance(data, dict)
            
            # Check that files were opened for reading and writing
            self.assertEqual(mock_open.call_count, 2)

class TestDatabaseHandler(unittest.TestCase):
    """Tests for the DatabaseHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'type': 'sqlite',
            'path': ':memory:'  # Use in-memory database for testing
        }
        
        # Mock the Path.parent.mkdir method
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            self.db_handler = DatabaseHandler(self.config)
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.db_handler.db_type, 'sqlite')
        self.assertEqual(str(self.db_handler.db_path), ':memory:')
    
    def test_insert_document(self):
        """Test document insertion."""
        # Test insertion
        doc_id = self.db_handler.insert_document(
            'resume',
            'test.pdf',
            {
                'candidate_name': 'Test Candidate',
                'skills': ['Python', 'SQL']
            }
        )
        
        # Check that an ID was returned
        self.assertIsInstance(doc_id, int)
        self.assertGreater(doc_id, 0)
    
    def test_get_document(self):
        """Test document retrieval."""
        # Insert a document
        doc_id = self.db_handler.insert_document(
            'resume',
            'test.pdf',
            {
                'candidate_name': 'Test Candidate',
                'skills': ['Python', 'SQL']
            }
        )
        
        # Retrieve the document
        doc = self.db_handler.get_document(doc_id)
        
        # Check that the document was retrieved
        self.assertIsInstance(doc, dict)
        self.assertEqual(doc['document_type'], 'resume')
        self.assertEqual(doc['file_name'], 'test.pdf')
        self.assertEqual(doc['content']['candidate_name'], 'Test Candidate')
    
    def test_query_documents(self):
        """Test document querying."""
        # Insert some documents
        self.db_handler.insert_document(
            'resume',
            'test1.pdf',
            {
                'candidate_name': 'Test Candidate 1',
                'skills': ['Python', 'SQL']
            }
        )
        self.db_handler.insert_document(
            'resume',
            'test2.pdf',
            {
                'candidate_name': 'Test Candidate 2',
                'skills': ['Java', 'C++']
            }
        )
        self.db_handler.insert_document(
            'job_description',
            'job1.pdf',
            {
                'job_title': 'Software Engineer',
                'required_qualifications': ['Python', 'SQL']
            }
        )
        
        # Query resumes
        resumes = self.db_handler.query_documents('resume')
        
        # Check that the correct number of documents were returned
        self.assertEqual(len(resumes), 2)
        
        # Query job descriptions
        jobs = self.db_handler.query_documents('job_description')
        
        # Check that the correct number of documents were returned
        self.assertEqual(len(jobs), 1)
        
        # Query with limit
        limited = self.db_handler.query_documents('resume', limit=1)
        
        # Check that the correct number of documents were returned
        self.assertEqual(len(limited), 1)

if __name__ == '__main__':
    unittest.main()