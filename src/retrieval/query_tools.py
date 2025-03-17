"""
Query Tools module for defining LLM agent tools for HR data retrieval.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable

from ..utils.logger import get_logger
from .database_connector import DatabaseConnector

logger = get_logger(__name__)

class QueryTools:
    """Class for defining LLM agent tools for HR data retrieval."""
    
    def __init__(self, db_connector: DatabaseConnector, config: Dict):
        """
        Initialize the query tools with database connector and configuration.
        
        Args:
            db_connector: Database connector instance
            config: Configuration dictionary
        """
        self.db = db_connector
        self.config = config
        
        # Load query rewrite prompt
        prompt_path = Path(os.environ.get('CONFIG_DIR', 'config')) / 'prompts' / 'query_rewrite_prompt.txt'
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.query_rewrite_prompt = f.read()
    
    def rewrite_query(self, user_query: str) -> Dict[str, Any]:
        """
        Rewrite a natural language query into a structured format.
        
        Args:
            user_query: Natural language query from the user
            
        Returns:
            Structured query as a dictionary
        """
        logger.info(f"Rewriting query: {user_query}")
        
        # Placeholder for actual LLM call
        # Example implementation:
        # response = openai.ChatCompletion.create(
        #     model=self.config.get('model_name', 'gpt-4'),
        #     messages=[
        #         {"role": "system", "content": self.query_rewrite_prompt},
        #         {"role": "user", "content": user_query}
        #     ],
        #     temperature=0.1
        # )
        # structured_query = json.loads(response.choices[0].message.content)
        
        # For now, return a placeholder
        structured_query = {
            "document_type": "resume",
            "filters": {
                "skills": "Python"
            },
            "fields": ["candidate_name", "contact_info", "skills"],
            "sort_by": {"education.graduation_date": "desc"},
            "limit": 5
        }
        
        return structured_query
    
    def search_resumes(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for resumes matching the query.
        
        Args:
            query: Structured query dictionary
            
        Returns:
            List of matching resumes
        """
        logger.info("Searching for resumes")
        return self.db.search_documents("resume", query.get("filters", {}), 
                                       query.get("fields", []), 
                                       query.get("sort_by", {}),
                                       query.get("limit", 10))
    
    def search_job_descriptions(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for job descriptions matching the query.
        
        Args:
            query: Structured query dictionary
            
        Returns:
            List of matching job descriptions
        """
        logger.info("Searching for job descriptions")
        return self.db.search_documents("job_description", query.get("filters", {}), 
                                       query.get("fields", []), 
                                       query.get("sort_by", {}),
                                       query.get("limit", 10))
    
    def search_performance_reviews(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for performance reviews matching the query.
        
        Args:
            query: Structured query dictionary
            
        Returns:
            List of matching performance reviews
        """
        logger.info("Searching for performance reviews")
        return self.db.search_documents("performance_review", query.get("filters", {}), 
                                       query.get("fields", []), 
                                       query.get("sort_by", {}),
                                       query.get("limit", 10))
    
    def get_tool_map(self) -> Dict[str, Callable]:
        """
        Get a mapping of tool names to functions.
        
        Returns:
            Dictionary mapping tool names to functions
        """
        return {
            "search_resumes": self.search_resumes,
            "search_job_descriptions": self.search_job_descriptions,
            "search_performance_reviews": self.search_performance_reviews
        }
    
    def execute_query(self, user_query: str) -> Dict[str, Any]:
        """
        Execute a natural language query and return results.
        
        Args:
            user_query: Natural language query from the user
            
        Returns:
            Query results
        """
        # Rewrite the query
        structured_query = self.rewrite_query(user_query)
        
        # Determine which tool to use based on document_type
        document_type = structured_query.get("document_type", "").lower()
        
        if document_type == "resume":
            results = self.search_resumes(structured_query)
        elif document_type in ["job_description", "job"]:
            results = self.search_job_descriptions(structured_query)
        elif document_type in ["performance_review", "review"]:
            results = self.search_performance_reviews(structured_query)
        else:
            logger.warning(f"Unknown document type: {document_type}")
            results = []
            
        return {
            "original_query": user_query,
            "structured_query": structured_query,
            "results": results,
            "result_count": len(results)
        }