"""
Database module for HR Intelligence.

This module provides a hybrid database solution for storing and searching resume data,
combining the strengths of structured data storage with vector-based semantic search.
"""

from .schema import (
    Candidate,
    ContactInfo,
    Education,
    WorkExperience,
    SearchQuery,
    SearchResult
)
from .duckdb_handler import DuckDBHandler
from .chroma_handler import ChromaDBHandler
from .hybrid_search import HybridSearchHandler

__all__ = [
    'Candidate',
    'ContactInfo',
    'Education',
    'WorkExperience',
    'SearchQuery',
    'SearchResult',
    'DuckDBHandler',
    'ChromaDBHandler',
    'HybridSearchHandler'
]
