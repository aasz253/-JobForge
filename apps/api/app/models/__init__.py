"""Re-export all SQLAlchemy models so Base.metadata sees them."""

from .user import User, Session, CandidateProfile, Setting  # noqa: F401
from .career import (  # noqa: F401
    Skill,
    CandidateSkill,
    Project,
    ProjectEvidence,
    CvDocument,
    CvVersion,
    ContentDraft,
)
from .jobs import (  # noqa: F401
    JobSource,
    Job,
    Application,
    ApplicationAnswer,
    CoverLetter,
    Followup,
    Interview,
    Recruiter,
    Contact,
)
from .finance import FinancialGoal, IncomeRecord  # noqa: F401
from .systems import AuditLog, EmailRecord, EmailEvent  # noqa: F401

__all__ = [
    "User",
    "Session",
    "CandidateProfile",
    "Setting",
    "Skill",
    "CandidateSkill",
    "Project",
    "ProjectEvidence",
    "CvDocument",
    "CvVersion",
    "ContentDraft",
    "JobSource",
    "Job",
    "Application",
    "ApplicationAnswer",
    "CoverLetter",
    "Followup",
    "Interview",
    "Recruiter",
    "Contact",
    "FinancialGoal",
    "IncomeRecord",
    "AuditLog",
    "EmailRecord",
    "EmailEvent",
]