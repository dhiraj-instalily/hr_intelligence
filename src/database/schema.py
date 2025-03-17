"""
Database schema definitions for the HR Intelligence system.
"""

from datetime import date
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4

class ContactInfo(BaseModel):
    """Contact information for a candidate."""
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None

class Education(BaseModel):
    """Education information for a candidate."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    institution: str
    degree: str
    dates: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[float] = None

    # Normalized fields for search
    normalized_institution: Optional[str] = None

class WorkExperience(BaseModel):
    """Work experience information for a candidate."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    company: str
    role: str
    dates: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    responsibilities: List[str] = []

    # Normalized fields for search
    normalized_company: Optional[str] = None
    normalized_role: Optional[str] = None

class Candidate(BaseModel):
    """Candidate information extracted from a resume."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_type: str = "resume"
    candidate_name: str
    contact_info: ContactInfo
    education: List[Education] = []
    work_experience: List[WorkExperience] = []
    skills: List[str] = []
    certifications: List[str] = []
    summary: Optional[str] = None
    raw_text: Optional[str] = None

    # Embedding fields
    embedding_text: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

class SearchQuery(BaseModel):
    """Search query parameters."""
    text: Optional[str] = None
    skills: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    education: Optional[List[str]] = None
    experience_years: Optional[int] = None
    limit: int = 10
    offset: int = 0

    # Semantic search parameters
    semantic_weight: float = 0.6
    fuzzy_weight: float = 0.3
    exact_weight: float = 0.1

class SearchResult(BaseModel):
    """Search result with candidate and score."""
    candidate: Candidate
    score: float
    match_details: Dict[str, Any] = {}
