"""JobSource interface — the modular contract every job source implements.

Sources never violate platform policies. A source is only usable when its
access method (public RSS, first-party API, manual entry) is permitted by the
platform and its terms of service.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

from jobforge_shared.constants import (
    EmploymentType,
    ExperienceLevel,
    JobSourceType,
    RemoteStatus,
)


@dataclass
class NormalizedJob:
    """The canonical normalized job record (see section 10 of the spec)."""

    source: str
    source_url: str
    application_url: str
    company: str
    title: str
    description: str
    location: str = ""
    country: str = ""
    remote_status: RemoteStatus | str = RemoteStatus.UNKNOWN
    employment_type: EmploymentType | str = EmploymentType.UNKNOWN
    experience_level: ExperienceLevel | str = ExperienceLevel.UNKNOWN
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = ""
    skills: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    posted_at: datetime | None = None
    deadline: datetime | None = None
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    external_id: str = ""
    hash: str = ""
    raw: dict = field(default_factory=dict)


class JobSource(ABC):
    """Contract implemented by every concrete job source plugin."""

    name: str = "abstract"
    source_type: JobSourceType = JobSourceType.MANUAL
    base_url: str = ""
    enabled: bool = True
    authentication_required: bool = False
    scraping_allowed: bool = True  # only used when the platform permits it
    rate_limit: int = 0  # requests per hour; 0 = no known limit

    @abstractmethod
    def fetch_jobs(self, **kwargs) -> list[NormalizedJob]:
        """Fetch jobs from this source. Must return normalizable jobs."""

    def normalize_job(self, raw_job: dict) -> NormalizedJob:
        """Transform a source-specific record into the canonical shape."""
        raise NotImplementedError

    def health_check(self) -> bool:
        """Return whether the source appears reachable/healthy."""
        return True