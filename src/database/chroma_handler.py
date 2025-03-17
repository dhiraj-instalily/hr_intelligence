"""
ChromaDB handler for vector storage and semantic search.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import chromadb
import chromadb.errors
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from ..utils.logger import get_logger
from .schema import Candidate, SearchQuery

logger = get_logger(__name__)

class ChromaDBHandler:
    """Handler for ChromaDB vector database operations."""

    def __init__(self,
                 db_path: str = "data/chroma_db",
                 collection_name: str = "candidates",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the ChromaDB handler.

        Args:
            db_path: Path to the ChromaDB directory
            collection_name: Name of the collection to use
            embedding_model: Name of the sentence transformer model to use
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model

        # Ensure parent directory exists
        self.db_path.parent.mkdir(exist_ok=True, parents=True)

        # Initialize database connection
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the database and create collection if it doesn't exist."""
        logger.info(f"Initializing ChromaDB at {self.db_path}")

        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model_name
        )

        # Connect to database
        self.client = chromadb.PersistentClient(path=str(self.db_path))

        # Create or get collection
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Using existing collection: {self.collection_name}")
        except chromadb.errors.InvalidCollectionException:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Created new collection: {self.collection_name}")

    def insert_candidate(self, candidate: Candidate) -> str:
        """
        Insert a candidate into the vector database.

        Args:
            candidate: Candidate object to insert

        Returns:
            ID of the inserted candidate
        """
        logger.info(f"Inserting candidate into vector store: {candidate.candidate_name}")

        # Generate embedding text if not provided
        if not candidate.embedding_text:
            embedding_text = self._create_embedding_text(candidate)
        else:
            embedding_text = candidate.embedding_text

        # Create metadata
        metadata = {
            "candidate_name": candidate.candidate_name,
            "skills": json.dumps(candidate.skills),
            "companies": json.dumps([exp.company for exp in candidate.work_experience]),
            "roles": json.dumps([exp.role for exp in candidate.work_experience]),
            "education": json.dumps([edu.institution for edu in candidate.education])
        }

        # Add to collection
        self.collection.add(
            ids=[candidate.id],
            documents=[embedding_text],
            metadatas=[metadata]
        )

        return candidate.id

    def _create_embedding_text(self, candidate: Candidate) -> str:
        """
        Create optimized text for semantic search.

        Args:
            candidate: Candidate object

        Returns:
            Text optimized for embedding
        """
        # Format work experience
        work_experience = "\n".join(
            f"Role: {exp.role} at {exp.company}. Responsibilities: {' '.join(exp.responsibilities)}"
            for exp in candidate.work_experience
        )

        # Format education
        education = "\n".join(
            f"Degree: {edu.degree} at {edu.institution}"
            for edu in candidate.education
        )

        # Create embedding text
        return f"""
        Candidate: {candidate.candidate_name}
        Skills: {", ".join(candidate.skills)}
        Education: {education}
        Experience: {work_experience}
        Certifications: {", ".join(candidate.certifications)}
        """

    def semantic_search(self, query: SearchQuery) -> List[Tuple[str, float]]:
        """
        Perform a semantic search for candidates.

        Args:
            query: Search query parameters

        Returns:
            List of (candidate_id, score) tuples
        """
        logger.info(f"Performing semantic search with query: {query.text}")

        # Build where clause for metadata filtering
        where_clause = {}

        if query.skills:
            # For each skill, check if it's in the skills list
            # This is a simplistic approach - in a real system you'd use proper filtering
            for skill in query.skills:
                where_clause[f"skills"] = {"$contains": skill}

        # Execute query
        results = self.collection.query(
            query_texts=[query.text],
            n_results=query.limit + query.offset,
            where=where_clause if where_clause else None
        )

        # Process results
        scored_candidates = []

        if results["ids"] and results["ids"][0]:
            for i, candidate_id in enumerate(results["ids"][0]):
                score = results["distances"][0][i] if "distances" in results and results["distances"] else 0.0
                # Convert distance to similarity score (1.0 - distance)
                similarity = 1.0 - score
                scored_candidates.append((candidate_id, similarity))

        # Apply offset
        return scored_candidates[query.offset:query.offset + query.limit]

    def delete_candidate(self, candidate_id: str) -> bool:
        """
        Delete a candidate from the vector database.

        Args:
            candidate_id: ID of the candidate to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[candidate_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting candidate {candidate_id}: {e}")
            return False

    def close(self):
        """Close the database connection."""
        # ChromaDB doesn't require explicit closing
        logger.info("ChromaDB connection closed")
