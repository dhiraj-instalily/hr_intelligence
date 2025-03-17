"""
Schema module for defining Pydantic models for data validation.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, validator

class Education(BaseModel):
    """Education model for resume data."""
    
    institution: str
    degree: str
    dates: str
    graduation_date: Optional[str] = None
    gpa: Optional[float] = None
    
    @validator('graduation_date', pre=True, always=False)
    def parse_graduation_date(cls, v):
        """Parse graduation date from dates if not provided."""
        if v is None:
            return None
        return v

class WorkExperience(BaseModel):
    """Work experience model for resume data."""
    
    company: str
    role: str
    dates: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities: List[str]
    
    @validator('start_date', 'end_date', pre=True, always=False)
    def parse_dates(cls, v):
        """Parse start and end dates from dates if not provided."""
        if v is None:
            return None
        return v

class ContactInfo(BaseModel):
    """Contact information model."""
    
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None

class Resume(BaseModel):
    """Resume model for validation."""
    
    document_type: str = "resume"
    candidate_name: str
    contact_info: ContactInfo
    education: List[Education]
    work_experience: List[WorkExperience]
    skills: List[str]
    certifications: Optional[List[str]] = None
    summary: Optional[str] = None
    
    @validator('document_type')
    def validate_document_type(cls, v):
        """Validate document type is 'resume'."""
        if v != "resume":
            raise ValueError("Document type must be 'resume'")
        return v

class JobLevel(str, Enum):
    """Job level enumeration."""
    
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"

class JobDescription(BaseModel):
    """Job description model for validation."""
    
    document_type: str = "job_description"
    job_title: str
    department: str
    job_level: Optional[JobLevel] = None
    required_qualifications: List[str]
    preferred_qualifications: Optional[List[str]] = None
    responsibilities: List[str]
    salary_range: Optional[Dict[str, float]] = None
    location: Optional[str] = None
    remote: Optional[bool] = None
    
    @validator('document_type')
    def validate_document_type(cls, v):
        """Validate document type is 'job_description'."""
        if v != "job_description":
            raise ValueError("Document type must be 'job_description'")
        return v

class PerformanceRating(str, Enum):
    """Performance rating enumeration."""
    
    EXCEPTIONAL = "exceptional"
    EXCEEDS_EXPECTATIONS = "exceeds_expectations"
    MEETS_EXPECTATIONS = "meets_expectations"
    NEEDS_IMPROVEMENT = "needs_improvement"
    UNSATISFACTORY = "unsatisfactory"

class PerformanceMetric(BaseModel):
    """Performance metric model."""
    
    name: str
    rating: PerformanceRating
    comments: Optional[str] = None

class PerformanceReview(BaseModel):
    """Performance review model for validation."""
    
    document_type: str = "performance_review"
    employee_name: str
    employee_id: Optional[str] = None
    review_period: str
    review_date: str
    metrics: List[PerformanceMetric]
    strengths: List[str]
    areas_for_improvement: List[str]
    overall_rating: PerformanceRating
    manager_comments: Optional[str] = None
    
    @validator('document_type')
    def validate_document_type(cls, v):
        """Validate document type is 'performance_review'."""
        if v != "performance_review":
            raise ValueError("Document type must be 'performance_review'")
        return v

class QueryFilter(BaseModel):
    """Query filter model."""
    
    document_type: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    fields: Optional[List[str]] = None
    sort_by: Optional[Dict[str, str]] = None
    limit: int = 10