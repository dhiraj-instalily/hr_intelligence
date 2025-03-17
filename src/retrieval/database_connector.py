"""
Database Connector module for querying the HR database.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseConnector:
    """Class for connecting to and querying the HR database."""
    
    def __init__(self, config: Dict):
        """
        Initialize the database connector with configuration.
        
        Args:
            config: Configuration dictionary with database settings
        """
        self.config = config
        self.db_type = config.get('type', 'sqlite')
        self.db_path = Path(config.get('path', '../data/hr_database.db'))
        
        # Initialize database connection
        self._connect_db()
        
    def _connect_db(self):
        """Connect to the database."""
        logger.info(f"Connecting to {self.db_type} database at {self.db_path}")
        
        if self.db_type == 'sqlite':
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
        else:
            logger.error(f"Unsupported database type: {self.db_type}")
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def search_documents(self, 
                         document_type: str, 
                         filters: Dict[str, Any] = None, 
                         fields: List[str] = None, 
                         sort_by: Dict[str, str] = None, 
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents in the database.
        
        Args:
            document_type: Type of document to search for
            filters: Dictionary of filters to apply
            fields: List of fields to return (None for all)
            sort_by: Dictionary of field to sort direction
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        logger.info(f"Searching for {document_type} documents with filters: {filters}")
        
        # Start building the query
        query = "SELECT id, document_type, file_name, content_json FROM documents WHERE document_type = ?"
        params = [document_type]
        
        # Add filters
        if filters:
            # In a real implementation, this would be more sophisticated
            # For now, we'll just do a simple JSON substring search
            for key, value in filters.items():
                # This is a simplistic approach - in a real system you'd use proper JSON querying
                query += f" AND content_json LIKE ?"
                params.append(f"%\"{key}\": \"{value}\"%")
        
        # Add sorting
        if sort_by:
            # Again, this is simplistic - real implementation would be more sophisticated
            for field, direction in sort_by.items():
                query += f" ORDER BY content_json"  # This is a placeholder
        
        # Add limit
        query += " LIMIT ?"
        params.append(limit)
        
        # Execute the query
        self.cursor.execute(query, params)
        
        # Process results
        results = []
        for row in self.cursor.fetchall():
            content = json.loads(row['content_json'])
            
            # Filter fields if specified
            if fields:
                filtered_content = {}
                for field in fields:
                    if field in content:
                        filtered_content[field] = content[field]
                content = filtered_content
            
            results.append({
                "id": row['id'],
                "document_type": row['document_type'],
                "file_name": row['file_name'],
                "content": content
            })
            
        return results
    
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
        
        row = self.cursor.fetchone()
        if row is None:
            return None
            
        content = json.loads(row['content_json'])
        
        return {
            "id": document_id,
            "document_type": row['document_type'],
            "file_name": row['file_name'],
            "content": content
        }
    
    def execute_raw_query(self, query: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query results
        """
        logger.info(f"Executing raw query: {query}")
        
        if params is None:
            params = []
            
        self.cursor.execute(query, params)
        
        results = []
        for row in self.cursor.fetchall():
            result = dict(row)
            
            # Parse content_json if present
            if 'content_json' in result:
                result['content'] = json.loads(result['content_json'])
                del result['content_json']
                
            results.append(result)
            
        return results
    
    def close(self):
        """Close the database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info("Database connection closed")