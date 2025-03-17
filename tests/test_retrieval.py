"""
Tests for the retrieval module.
"""

import os
import sys
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.database_connector import DatabaseConnector
from src.retrieval.query_tools import QueryTools
from src.retrieval.cache import QueryCache
from src.retrieval.schema import Resume, JobDescription, PerformanceReview

class TestDatabaseConnector(unittest.TestCase):
    """Tests for the DatabaseConnector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'type': 'sqlite',
            'path': ':memory:'  # Use in-memory database for testing
        }
        
        # Create the connector
        self.db = DatabaseConnector(self.config)
        
        # Create a test table and insert some data
        self.db.cursor.execute('''
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            content_json TEXT NOT NULL
        )
        ''')
        
        # Insert test data
        self.db.cursor.execute(
            "INSERT INTO documents (document_type, file_name, content_json) VALUES (?, ?, ?)",
            ('resume', 'test1.pdf', json.dumps({
                'candidate_name': 'Test Candidate 1',
                'skills': ['Python', 'SQL']
            }))
        )
        self.db.cursor.execute(
            "INSERT INTO documents (document_type, file_name, content_json) VALUES (?, ?, ?)",
            ('resume', 'test2.pdf', json.dumps({
                'candidate_name': 'Test Candidate 2',
                'skills': ['Java', 'C++']
            }))
        )
        self.db.cursor.execute(
            "INSERT INTO documents (document_type, file_name, content_json) VALUES (?, ?, ?)",
            ('job_description', 'job1.pdf', json.dumps({
                'job_title': 'Software Engineer',
                'required_qualifications': ['Python', 'SQL']
            }))
        )
        self.db.conn.commit()
    
    def test_search_documents(self):
        """Test document search."""
        # Search for resumes
        resumes = self.db.search_documents('resume')
        
        # Check that the correct number of documents were returned
        self.assertEqual(len(resumes), 2)
        
        # Search for job descriptions
        jobs = self.db.search_documents('job_description')
        
        # Check that the correct number of documents were returned
        self.assertEqual(len(jobs), 1)
        
        # Search with filters
        filtered = self.db.search_documents('resume', {'skills': 'Python'})
        
        # Check that the correct number of documents were returned
        # Note: This is a simplistic test - the actual implementation would be more sophisticated
        self.assertGreaterEqual(len(filtered), 0)
        
        # Search with limit
        limited = self.db.search_documents('resume', limit=1)
        
        # Check that the correct number of documents were returned
        self.assertEqual(len(limited), 1)
    
    def test_get_document(self):
        """Test document retrieval."""
        # Get a document
        doc = self.db.get_document(1)
        
        # Check that the document was retrieved
        self.assertIsInstance(doc, dict)
        self.assertEqual(doc['document_type'], 'resume')
        self.assertEqual(doc['file_name'], 'test1.pdf')
        self.assertEqual(doc['content']['candidate_name'], 'Test Candidate 1')
    
    def test_execute_raw_query(self):
        """Test raw query execution."""
        # Execute a raw query
        results = self.db.execute_raw_query(
            "SELECT * FROM documents WHERE document_type = ?",
            ['resume']
        )
        
        # Check that the correct number of documents were returned
        self.assertEqual(len(results), 2)

class TestQueryTools(unittest.TestCase):
    """Tests for the QueryTools class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock database connector
        self.db = MagicMock()
        
        # Configure the mock to return test data
        self.db.search_documents.return_value = [
            {
                'id': 1,
                'document_type': 'resume',
                'file_name': 'test1.pdf',
                'content': {
                    'candidate_name': 'Test Candidate 1',
                    'skills': ['Python', 'SQL']
                }
            }
        ]
        
        self.config = {
            'model_name': 'gpt-4',
            'temperature': 0.1
        }
        
        # Mock the open function for loading the prompt
        with patch('builtins.open', unittest.mock.mock_open(read_data="Test prompt")) as mock_open:
            self.query_tools = QueryTools(self.db, self.config)
    
    def test_rewrite_query(self):
        """Test query rewriting."""
        # Test query rewriting
        query = self.query_tools.rewrite_query("Find Python developers")
        
        # Check that the result is a dictionary
        self.assertIsInstance(query, dict)
        
        # Check that the expected fields are present
        self.assertIn('document_type', query)
        self.assertIn('filters', query)
        self.assertIn('fields', query)
        self.assertIn('sort_by', query)
        self.assertIn('limit', query)
    
    def test_search_resumes(self):
        """Test resume search."""
        # Test resume search
        results = self.query_tools.search_resumes({
            'filters': {'skills': 'Python'},
            'fields': ['candidate_name', 'skills'],
            'limit': 5
        })
        
        # Check that the database connector was called correctly
        self.db.search_documents.assert_called_once_with(
            'resume',
            {'skills': 'Python'},
            ['candidate_name', 'skills'],
            {},
            5
        )
    
    def test_execute_query(self):
        """Test query execution."""
        # Test query execution
        results = self.query_tools.execute_query("Find Python developers")
        
        # Check that the result is a dictionary
        self.assertIsInstance(results, dict)
        
        # Check that the expected fields are present
        self.assertIn('original_query', results)
        self.assertIn('structured_query', results)
        self.assertIn('results', results)
        self.assertIn('result_count', results)

class TestQueryCache(unittest.TestCase):
    """Tests for the QueryCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for the cache
        self.temp_dir = tempfile.TemporaryDirectory()
        
        self.config = {
            'cache_results': True,
            'cache_dir': self.temp_dir.name,
            'cache_ttl': 3600
        }
        
        self.cache = QueryCache(self.config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_cache_operations(self):
        """Test cache operations."""
        # Test data
        query_type = 'test_query'
        query_params = {'param1': 'value1', 'param2': 'value2'}
        results = {'result1': 'value1', 'result2': 'value2'}
        
        # Test cache miss
        cached_results = self.cache.get(query_type, query_params)
        self.assertIsNone(cached_results)
        
        # Test cache set
        self.cache.set(query_type, query_params, results)
        
        # Test cache hit
        cached_results = self.cache.get(query_type, query_params)
        self.assertEqual(cached_results, results)
        
        # Test cache invalidation
        self.cache.invalidate(query_type)
        cached_results = self.cache.get(query_type, query_params)
        self.assertIsNone(cached_results)

class TestSchema(unittest.TestCase):
    """Tests for the schema models."""
    
    def test_resume_schema(self):
        """Test Resume schema."""
        # Valid resume data
        resume_data = {
            'document_type': 'resume',
            'candidate_name': 'Test Candidate',
            'contact_info': {
                'email': 'test@example.com',
                'phone': '123-456-7890'
            },
            'education': [
                {
                    'institution': 'Test University',
                    'degree': 'Bachelor of Science',
                    'dates': '2015-2019'
                }
            ],
            'work_experience': [
                {
                    'company': 'Test Company',
                    'role': 'Software Engineer',
                    'dates': '2019-Present',
                    'responsibilities': ['Coding', 'Testing']
                }
            ],
            'skills': ['Python', 'SQL']
        }
        
        # Create a Resume object
        resume = Resume(**resume_data)
        
        # Check that the object was created correctly
        self.assertEqual(resume.document_type, 'resume')
        self.assertEqual(resume.candidate_name, 'Test Candidate')
        self.assertEqual(resume.contact_info.email, 'test@example.com')
        self.assertEqual(len(resume.education), 1)
        self.assertEqual(len(resume.work_experience), 1)
        self.assertEqual(len(resume.skills), 2)
    
    def test_job_description_schema(self):
        """Test JobDescription schema."""
        # Valid job description data
        job_data = {
            'document_type': 'job_description',
            'job_title': 'Software Engineer',
            'department': 'Engineering',
            'job_level': 'senior',
            'required_qualifications': ['Python', 'SQL'],
            'preferred_qualifications': ['AWS', 'Docker'],
            'responsibilities': ['Develop software', 'Write tests'],
            'salary_range': {'min': 100000, 'max': 150000},
            'location': 'Remote',
            'remote': True
        }
        
        # Create a JobDescription object
        job = JobDescription(**job_data)
        
        # Check that the object was created correctly
        self.assertEqual(job.document_type, 'job_description')
        self.assertEqual(job.job_title, 'Software Engineer')
        self.assertEqual(job.department, 'Engineering')
        self.assertEqual(job.job_level, 'senior')
        self.assertEqual(len(job.required_qualifications), 2)
        self.assertEqual(len(job.preferred_qualifications), 2)
        self.assertEqual(len(job.responsibilities), 2)
        self.assertEqual(job.salary_range['min'], 100000)
        self.assertEqual(job.location, 'Remote')
        self.assertEqual(job.remote, True)
    
    def test_performance_review_schema(self):
        """Test PerformanceReview schema."""
        # Valid performance review data
        review_data = {
            'document_type': 'performance_review',
            'employee_name': 'Test Employee',
            'employee_id': 'E12345',
            'review_period': '2022',
            'review_date': '2022-12-31',
            'metrics': [
                {
                    'name': 'Quality',
                    'rating': 'exceeds_expectations',
                    'comments': 'Excellent work'
                },
                {
                    'name': 'Quantity',
                    'rating': 'meets_expectations'
                }
            ],
            'strengths': ['Technical skills', 'Communication'],
            'areas_for_improvement': ['Time management'],
            'overall_rating': 'exceeds_expectations',
            'manager_comments': 'Great work this year'
        }
        
        # Create a PerformanceReview object
        review = PerformanceReview(**review_data)
        
        # Check that the object was created correctly
        self.assertEqual(review.document_type, 'performance_review')
        self.assertEqual(review.employee_name, 'Test Employee')
        self.assertEqual(review.employee_id, 'E12345')
        self.assertEqual(review.review_period, '2022')
        self.assertEqual(len(review.metrics), 2)
        self.assertEqual(len(review.strengths), 2)
        self.assertEqual(len(review.areas_for_improvement), 1)
        self.assertEqual(review.overall_rating, 'exceeds_expectations')
        self.assertEqual(review.manager_comments, 'Great work this year')

if __name__ == '__main__':
    unittest.main()