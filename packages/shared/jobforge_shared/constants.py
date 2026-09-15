"""Shared enums and constants for JobForge.

Central single source of truth for domain vocabulary used across the API,
packages, and frontend contracts. Lives in its own installable package so
that all JobForge components stay consistent.
"""

from __future__ import annotations

from enum import Enum

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class JobStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    QUALIFIED = "QUALIFIED"
    SAVED = "SAVED"
    PREPARING = "PREPARING"
    READY = "READY"
    APPLIED = "APPLIED"
    APPLICATION_RECEIVED = "APPLICATION_RECEIVED"
    RECRUITER_CONTACTED = "RECRUITER_CONTACTED"
    SCREENING = "SCREENING"
    TECHNICAL_INTERVIEW = "TECHNICAL_INTERVIEW"
    FINAL_INTERVIEW = "FINAL_INTERVIEW"
    OFFER = "OFFER"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


# Stages shown on the kanban board
BOARD_COLUMNS: list[str] = [
    "DISCOVERED",
    "QUALIFIED",
    "APPLIED",
    "INTERVIEW",
    "OFFER",
    "ACCEPTED",
]

BOARD_COLUMN_MEMBERS: dict[str, list[str]] = {
    "DISCOVERED": [JobStatus.DISCOVERED, JobStatus.SAVED],
    "QUALIFIED": [JobStatus.QUALIFIED, JobStatus.PREPARING, JobStatus.READY],
    "APPLIED": [JobStatus.APPLIED, JobStatus.APPLICATION_RECEIVED, JobStatus.RECRUITER_CONTACTED],
    "INTERVIEW": [JobStatus.SCREENING, JobStatus.TECHNICAL_INTERVIEW, JobStatus.FINAL_INTERVIEW],
    "OFFER": [JobStatus.OFFER],
    "ACCEPTED": [JobStatus.ACCEPTED],
}


class RemoteStatus(StrEnum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ON_SITE = "ON_SITE"
    UNKNOWN = "UNKNOWN"


class EmploymentType(StrEnum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    FREELANCE = "FREELANCE"
    INTERNSHIP = "INTERNSHIP"
    UNKNOWN = "UNKNOWN"


class ExperienceLevel(StrEnum):
    ENTRY = "ENTRY"
    JUNIOR = "JUNIOR"
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    UNKNOWN = "UNKNOWN"


class JobSourceType(StrEnum):
    API = "API"
    RSS = "RSS"
    COMPANY_CAREER_PAGE = "COMPANY_CAREER_PAGE"
    JOB_BOARD = "JOB_BOARD"
    MANUAL = "MANUAL"
    USER_URL = "USER_URL"
    EMAIL_JOB_ALERT = "EMAIL_JOB_ALERT"
    BROWSER = "BROWSER"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EmailCategory(StrEnum):
    APPLICATION_RECEIVED = "APPLICATION_RECEIVED"
    INTERVIEW_INVITATION = "INTERVIEW_INVITATION"
    TECHNICAL_ASSESSMENT = "TECHNICAL_ASSESSMENT"
    RECRUITER_CONTACT = "RECRUITER_CONTACT"
    FOLLOW_UP = "FOLLOW_UP"
    REJECTION = "REJECTION"
    OFFER = "OFFER"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    OTHER = "OTHER"


class ContactStatus(StrEnum):
    NEW = "NEW"
    CONNECTED = "CONNECTED"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    CLOSED = "CLOSED"


class IncomeCategory(StrEnum):
    EMPLOYMENT = "EMPLOYMENT"
    CONTRACT = "CONTRACT"
    FREELANCE = "FREELANCE"
    PRODUCT = "PRODUCT"
    OTHER = "OTHER"


class AiProvider(StrEnum):
    NONE = "none"
    LOCAL = "local"
    OPENROUTER = "openrouter"
    OPENAI_COMPATIBLE = "openai_compatible"


# Score band boundaries (0-100)
SCORE_BANDS: dict[str, tuple[int, int]] = {
    "PRIORITY": (90, 100),
    "STRONG": (80, 89),
    "GOOD": (70, 79),
    "POSSIBLE": (60, 69),
    "LOW": (0, 59),
}

SCORE_BAND_LABELS: dict[str, str] = {
    "PRIORITY": "Priority",
    "STRONG": "Strong match",
    "GOOD": "Good match",
    "POSSIBLE": "Possible",
    "LOW": "Low priority",
}


def score_label(score: int | float) -> str:
    """Return the human label for a 0-100 job score."""
    for band, (lo, hi) in SCORE_BANDS.items():
        if lo <= score <= hi:
            return SCORE_BAND_LABELS[band]
    return SCORE_BAND_LABELS["LOW"]


def score_band(score: int | float) -> str:
    for band, (lo, hi) in SCORE_BANDS.items():
        if lo <= score <= hi:
            return band
    return "LOW"


# ---------------------------------------------------------------------------
# Scoring weights (defaults; user configurable client-side / persisted)
# Total must equal 100.
# ---------------------------------------------------------------------------

DEFAULT_SCORE_WEIGHTS: dict[str, float] = {
    "ai_llm": 20.0,
    "devsecops": 20.0,
    "security": 15.0,
    "cloud": 10.0,
    "python_development": 10.0,
    "containers": 10.0,
    "remote_international": 5.0,
    "experience_fit": 5.0,
    "project_evidence": 5.0,
}

# ---------------------------------------------------------------------------
# Daily mission defaults (configurable)
# ---------------------------------------------------------------------------

DEFAULT_MISSION: dict[str, int] = {
    "jobs_discovered": 20,
    "jobs_qualified": 10,
    "applications": 5,
    "recruiter_connections": 5,
    "recruiter_messages": 2,
    "follow_ups": 3,
    "technical_content": 1,
}

# ---------------------------------------------------------------------------
# Follow-up schedule (days after submission) — configurable
# ---------------------------------------------------------------------------

DEFAULT_FOLLOWUP_SCHEDULE: list[int] = [5, 10, 20]

# ---------------------------------------------------------------------------
# Financial goal
# ---------------------------------------------------------------------------

DEFAULT_FINANCIAL_GOAL_AMOUNT = 1_000_000
DEFAULT_FINANCIAL_GOAL_CURRENCY = "KSh"

# ---------------------------------------------------------------------------
# Candidate fallback safeguarding
# ---------------------------------------------------------------------------

# Claims the AI may never emit without backing evidence in the candidate database.
PROHIBITED_UNSUPPORTED_CLAIMS: list[str] = [
    "experienced in Kubernetes production at scale",
    "managed a production cluster",
    "worked at",  # employer claims
    "certified",  # certification claims must be in profile
    "led a team",
    "years of experience",
]

DEFAULT_CV_VERSIONS: list[str] = [
    "AI DevSecOps",
    "DevSecOps / Cloud",
    "Cybersecurity",
    "Software Engineering",
]