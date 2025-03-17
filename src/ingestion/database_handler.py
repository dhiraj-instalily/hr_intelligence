"""
Database Handler module for storing extracted data in a database.
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseHandler:
    """Class for handling database operations."""
    
    def __init__(self, config: Dict):
        """
        Initialize the database handler with configuration.
        
        Args:
            config: Configuration dictionary with database settings
        """
        self.config = config
        self.db_type = config.get('type', 'sqlite')
        self.db_path = Path(config.get('path', '../data/hr_database.db'))
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Initialize database connection
        self._initialize_db()
        
    def _initialize_db(self):
        """Initialize the database and create tables if they don't exist."""
        logger.info(f"Initializing {self.db_type} database at {self.db_path}")
        
        if self.db_type == 'sqlite':
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create tables if they don't exist
            self._create_tables()
        else:
            logger.error(f"Unsupported database type: {self.db_type}")
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def _create_tables(self):
        """Create necessary tables in the database."""
        # Create documents table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            content_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create index on document_type for faster queries
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_type ON documents(document_type)
        ''')
        
        self.conn.commit()
        logger.info("Database tables created successfully")
    
    def insert_document(self, document_type: str, file_name: str, content: Dict[str, Any]) -> int:
        """
        Insert a document into the database.
        
        Args:
            document_type: Type of document (resume, job_description, etc.)
            file_name: Original file name
            content: Document content as a dictionary
            
        Returns:
            ID of the inserted document
        """
        logger.info(f"Inserting {document_type} document: {file_name}")
        
        content_json = json.dumps(content)
        
        self.cursor.execute(
            "INSERT INTO documents (document_type, file_name, content_json) VALUES (?, ?, ?)",
            (document_type, file_name, content_json)
        )
        self.conn.commit()
        
        return self.cursor.lastrowid
    
    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from the database by ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Document as a dictionary, or None if not found
        """
        self.cursor.execute(
            "SELECT document_type, file_name, content_json FROM documents WHERE id = ?",
            (document_id,)
        )
        
        result = self.cursor.fetchone()
        if result is None:
            return None
            
        document_type, file_name, content_json = result
        content = json.loads(content_json)
        
        return {
            "id": document_id,
            "document_type": document_type,
            "file_name": file_name,
            "content": content
        }
    
    def query_documents(self, document_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query documents from the database.
        
        Args:
            document_type: Optional filter by document type
            limit: Maximum number of documents to return
            
        Returns:
            List of documents as dictionaries
        """
        if document_type:
            self.cursor.execute(
                "SELECT id, document_type, file_name, content_json FROM documents WHERE document_type = ? LIMIT ?",
                (document_type, limit)
            )
        else:
            self.cursor.execute(
                "SELECT id, document_type, file_name, content_json FROM documents LIMIT ?",
                (limit,)
            )
            
        results = []
        for row in self.cursor.fetchall():
            doc_id, doc_type, file_name, content_json = row
            content = json.loads(content_json)
            
            results.append({
                "id": doc_id,
                "document_type": doc_type,
                "file_name": file_name,
                "content": content
            })
            
        return results
    
    def close(self):
        """Close the database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info("Database connection closed")