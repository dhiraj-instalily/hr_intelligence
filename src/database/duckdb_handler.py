"""
DuckDB handler for structured data storage with fuzzy search capabilities.
"""

import os
import json
import uuid
import duckdb
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from uuid import UUID, uuid4
from datetime import date, datetime
from rapidfuzz import fuzz, process

from ..utils.logger import get_logger
from .schema import Candidate, Education, WorkExperience, SearchQuery

logger = get_logger(__name__)

# SQL statements for database setup
CREATE_CANDIDATES_TABLE = """
CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY,
    candidate_name TEXT NOT NULL,
    document_type TEXT NOT NULL,
    contact_info JSON,
    education JSON,
    work_experience JSON,
    skills JSON,
    certifications JSON,
    summary TEXT,
    raw_text TEXT,
    embedding_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_WORK_EXPERIENCE_TABLE = """
CREATE TABLE IF NOT EXISTS work_experience (
    id TEXT PRIMARY KEY,
    candidate_id TEXT REFERENCES candidates(id),
    company TEXT NOT NULL,
    normalized_company TEXT,
    role TEXT NOT NULL,
    normalized_role TEXT,
    responsibilities TEXT,
    start_date DATE,
    end_date DATE
);
"""

CREATE_EDUCATION_TABLE = """
CREATE TABLE IF NOT EXISTS education (
    id TEXT PRIMARY KEY,
    candidate_id TEXT REFERENCES candidates(id),
    institution TEXT NOT NULL,
    normalized_institution TEXT,
    degree TEXT NOT NULL,
    graduation_date DATE,
    gpa FLOAT
);
"""

CREATE_SKILLS_TABLE = """
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    candidate_id TEXT REFERENCES candidates(id),
    skill TEXT NOT NULL
);
"""

class DuckDBHandler:
    """Handler for DuckDB database operations."""

    def __init__(self, db_path: str = "data/hr_database.duckdb"):
        """
        Initialize the DuckDB handler.

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = Path(db_path)

        # Ensure parent directory exists
        self.db_path.parent.mkdir(exist_ok=True, parents=True)

        # Initialize database connection
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the database and create tables if they don't exist."""
        logger.info(f"Initializing DuckDB database at {self.db_path}")

        # Connect to database
        self.conn = duckdb.connect(str(self.db_path))

        # Create tables
        self.conn.execute(CREATE_CANDIDATES_TABLE)
        self.conn.execute(CREATE_WORK_EXPERIENCE_TABLE)
        self.conn.execute(CREATE_EDUCATION_TABLE)
        self.conn.execute(CREATE_SKILLS_TABLE)

        # Create indexes for faster searches
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_candidate_name ON candidates(candidate_name);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_company ON work_experience(normalized_company);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_role ON work_experience(normalized_role);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_institution ON education(normalized_institution);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_skill ON skills(skill);")

        logger.info("Database tables and indexes created successfully")

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for better fuzzy matching.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Convert to lowercase
        normalized = text.lower()

        # Remove common suffixes
        for suffix in ["inc", "llc", "corp", "corporation", "ltd", "limited"]:
            normalized = normalized.replace(f" {suffix}", "")
            normalized = normalized.replace(f" {suffix}.", "")

        # Remove punctuation
        for char in ",.()":
            normalized = normalized.replace(char, "")

        return normalized.strip()

    def insert_candidate(self, candidate: Candidate) -> str:
        """
        Insert a candidate into the database.

        Args:
            candidate: Candidate to insert

        Returns:
            ID of the inserted candidate
        """
        logger.info(f"Inserting candidate: {candidate.candidate_name}")

        # Generate ID if not provided
        if not candidate.id:
            candidate.id = str(uuid4())

        # Generate embedding text if not provided
        if not candidate.embedding_text:
            candidate.embedding_text = self._create_embedding_text(candidate)

        # Normalize company and role names
        for exp in candidate.work_experience:
            # Add ID if missing
            if not hasattr(exp, 'id') or not exp.id:
                exp.id = str(uuid4())

            if not exp.normalized_company:
                exp.normalized_company = self._normalize_text(exp.company)
            if not exp.normalized_role:
                exp.normalized_role = self._normalize_text(exp.role)

        # Normalize institution names
        for edu in candidate.education:
            if not edu.normalized_institution:
                edu.normalized_institution = self._normalize_text(edu.institution)

        # Insert into candidates table
        self.conn.execute(
            """
            INSERT INTO candidates (
                id, candidate_name, document_type, contact_info, education,
                work_experience, skills, certifications, summary, raw_text, embedding_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate.id,
                candidate.candidate_name,
                candidate.document_type,
                json.dumps(candidate.contact_info.dict()),
                json.dumps([edu.dict() for edu in candidate.education]),
                json.dumps([exp.dict() for exp in candidate.work_experience]),
                json.dumps(candidate.skills),
                json.dumps(candidate.certifications),
                candidate.summary,
                candidate.raw_text,
                candidate.embedding_text
            )
        )

        # Insert work experience
        for i, exp in enumerate(candidate.work_experience):
            self.conn.execute(
                """
                INSERT INTO work_experience (
                    id, candidate_id, company, normalized_company, role, normalized_role,
                    responsibilities, start_date, end_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exp.id,
                    candidate.id,
                    exp.company,
                    exp.normalized_company,
                    exp.role,
                    exp.normalized_role,
                    json.dumps(exp.responsibilities),
                    exp.start_date,
                    exp.end_date
                )
            )

        # Insert education
        for i, edu in enumerate(candidate.education):
            self.conn.execute(
                """
                INSERT INTO education (
                    id, candidate_id, institution, normalized_institution, degree, graduation_date, gpa
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edu.id,
                    candidate.id,
                    edu.institution,
                    edu.normalized_institution,
                    edu.degree,
                    edu.graduation_date,
                    edu.gpa
                )
            )

        # Insert skills
        for skill in candidate.skills:
            self.conn.execute(
                "INSERT INTO skills (id, candidate_id, skill) VALUES (?, ?, ?)",
                (str(uuid4()), candidate.id, skill)
            )

        return candidate.id

    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """
        Retrieve a candidate from the database by ID.

        Args:
            candidate_id: ID of the candidate to retrieve

        Returns:
            Candidate object, or None if not found
        """
        result = self.conn.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()

        if not result:
            return None

        # Convert to dictionary
        candidate_dict = dict(zip(result.keys(), result))

        # Parse JSON fields
        candidate_dict["contact_info"] = json.loads(candidate_dict["contact_info"])
        candidate_dict["education"] = json.loads(candidate_dict["education"])
        candidate_dict["work_experience"] = json.loads(candidate_dict["work_experience"])
        candidate_dict["skills"] = json.loads(candidate_dict["skills"])
        candidate_dict["certifications"] = json.loads(candidate_dict["certifications"])

        # Create Candidate object
        return Candidate(**candidate_dict)

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

    def fuzzy_search(self, query: SearchQuery) -> List[Tuple[Candidate, float]]:
        """
        Perform a fuzzy search for candidates.

        Args:
            query: Search query parameters

        Returns:
            List of (candidate, score) tuples
        """
        logger.info(f"Performing fuzzy search with query: {query}")

        # Start with all candidates
        candidates_query = "SELECT * FROM candidates"
        params = []

        # Add filters for skills
        if query.skills:
            skill_placeholders = ", ".join(["?"] * len(query.skills))
            candidates_query = f"""
            SELECT c.* FROM candidates c
            JOIN skills s ON c.id = s.candidate_id
            WHERE s.skill IN ({skill_placeholders})
            GROUP BY c.id
            """
            params.extend(query.skills)

        # Execute query
        results = self.conn.execute(candidates_query, params).fetchall()

        # Convert to Candidate objects
        candidates = []
        for result in results:
            candidate_dict = dict(zip(result.keys(), result))

            # Parse JSON fields
            candidate_dict["contact_info"] = json.loads(candidate_dict["contact_info"])
            candidate_dict["education"] = json.loads(candidate_dict["education"])
            candidate_dict["work_experience"] = json.loads(candidate_dict["work_experience"])
            candidate_dict["skills"] = json.loads(candidate_dict["skills"])
            candidate_dict["certifications"] = json.loads(candidate_dict["certifications"])

            # Create Candidate object
            candidates.append(Candidate(**candidate_dict))

        # Perform fuzzy matching
        scored_candidates = []

        for candidate in candidates:
            score = 0.0
            match_count = 0

            # Match companies
            if query.companies:
                company_scores = []
                for company in query.companies:
                    for exp in candidate.work_experience:
                        company_score = fuzz.token_sort_ratio(company.lower(), exp.company.lower()) / 100.0
                        if company_score > 0.7:  # 70% similarity threshold
                            company_scores.append(company_score)

                if company_scores:
                    score += max(company_scores) * query.fuzzy_weight
                    match_count += 1

            # Match roles
            if query.roles:
                role_scores = []
                for role in query.roles:
                    for exp in candidate.work_experience:
                        role_score = fuzz.token_sort_ratio(role.lower(), exp.role.lower()) / 100.0
                        if role_score > 0.7:  # 70% similarity threshold
                            role_scores.append(role_score)

                if role_scores:
                    score += max(role_scores) * query.fuzzy_weight
                    match_count += 1

            # Match education
            if query.education:
                edu_scores = []
                for edu_query in query.education:
                    for edu in candidate.education:
                        edu_score = fuzz.token_sort_ratio(edu_query.lower(), edu.institution.lower()) / 100.0
                        if edu_score > 0.7:  # 70% similarity threshold
                            edu_scores.append(edu_score)

                if edu_scores:
                    score += max(edu_scores) * query.fuzzy_weight
                    match_count += 1

            # Match skills (exact match)
            if query.skills:
                skill_matches = set(query.skills).intersection(set(candidate.skills))
                if skill_matches:
                    skill_score = len(skill_matches) / len(query.skills)
                    score += skill_score * query.exact_weight
                    match_count += 1

            # Normalize score
            if match_count > 0:
                score /= match_count
                scored_candidates.append((candidate, score))

        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Apply limit and offset
        return scored_candidates[query.offset:query.offset + query.limit]

    def close(self):
        """Close the database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info("Database connection closed")
