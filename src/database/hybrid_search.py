"""
Hybrid search handler that combines DuckDB and ChromaDB for powerful search capabilities.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from uuid import uuid4

from ..utils.logger import get_logger
from .schema import Candidate, SearchQuery, SearchResult
from .duckdb_handler import DuckDBHandler
from .chroma_handler import ChromaDBHandler

logger = get_logger(__name__)

class HybridSearchHandler:
    """Handler for hybrid search operations combining structured and vector search."""

    def __init__(self,
                 duckdb_path: str = "data/hr_database.duckdb",
                 chroma_path: str = "data/chroma_db",
                 collection_name: str = "candidates",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the hybrid search handler.

        Args:
            duckdb_path: Path to the DuckDB database file
            chroma_path: Path to the ChromaDB directory
            collection_name: Name of the ChromaDB collection to use
            embedding_model: Name of the sentence transformer model to use
        """
        self.duckdb_handler = DuckDBHandler(db_path=duckdb_path)
        self.chroma_handler = ChromaDBHandler(
            db_path=chroma_path,
            collection_name=collection_name,
            embedding_model=embedding_model
        )

        logger.info("Hybrid search handler initialized")

    def insert_candidate(self, candidate: Candidate) -> str:
        """
        Insert a candidate into both databases.

        Args:
            candidate: Candidate object to insert

        Returns:
            ID of the inserted candidate
        """
        logger.info(f"Inserting candidate into both databases: {candidate.candidate_name}")

        # Generate ID if not provided
        if not candidate.id:
            candidate.id = str(uuid4())

        # Generate embedding text if not provided
        if not candidate.embedding_text:
            candidate.embedding_text = self.duckdb_handler._create_embedding_text(candidate)

        # Insert into DuckDB
        self.duckdb_handler.insert_candidate(candidate)

        # Insert into ChromaDB
        self.chroma_handler.insert_candidate(candidate)

        return candidate.id

    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """
        Retrieve a candidate from the database by ID.

        Args:
            candidate_id: ID of the candidate to retrieve

        Returns:
            Candidate object, or None if not found
        """
        return self.duckdb_handler.get_candidate(candidate_id)

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Perform a hybrid search for candidates.

        Args:
            query: Search query parameters

        Returns:
            List of search results with candidates and scores
        """
        logger.info(f"Performing hybrid search with query: {query}")

        results = []

        # Perform semantic search if text query is provided
        if query.text:
            semantic_results = self.chroma_handler.semantic_search(query)

            # Get candidate objects and create search results
            for candidate_id, score in semantic_results:
                candidate = self.duckdb_handler.get_candidate(candidate_id)
                if candidate:
                    results.append(SearchResult(
                        candidate=candidate,
                        score=score * query.semantic_weight,
                        match_details={"semantic_score": score}
                    ))

        # Perform fuzzy search
        fuzzy_results = self.duckdb_handler.fuzzy_search(query)

        # Add fuzzy search results
        for candidate, score in fuzzy_results:
            # Check if candidate is already in results
            existing_result = next((r for r in results if r.candidate.id == candidate.id), None)

            if existing_result:
                # Update existing result
                existing_result.score += score * query.fuzzy_weight
                existing_result.match_details["fuzzy_score"] = score
            else:
                # Add new result
                results.append(SearchResult(
                    candidate=candidate,
                    score=score * query.fuzzy_weight,
                    match_details={"fuzzy_score": score}
                ))

        # Sort by score (descending)
        results.sort(key=lambda x: x.score, reverse=True)

        # Apply limit and offset
        return results[query.offset:query.offset + query.limit]

    def delete_candidate(self, candidate_id: str) -> bool:
        """
        Delete a candidate from both databases.

        Args:
            candidate_id: ID of the candidate to delete

        Returns:
            True if successful, False otherwise
        """
        # Delete from ChromaDB
        chroma_success = self.chroma_handler.delete_candidate(candidate_id)

        # TODO: Implement delete in DuckDB handler
        # duckdb_success = self.duckdb_handler.delete_candidate(candidate_id)

        return chroma_success

    def close(self):
        """Close the database connections."""
        self.duckdb_handler.close()
        self.chroma_handler.close()
        logger.info("Database connections closed")
