"""Job-related schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImportUrlIn(BaseModel):
    url: str = Field(min_length=8, max_length=800)


class ImportManualIn(BaseModel):
    company: str = Field(default="", max_length=200)
    title: str = Field(default="", max_length=300)
    description: str = Field(min_length=20, max_length=200_000)
    url: str = Field(default="", max_length=800)
    application_url: str = Field(default="", max_length=800)
    source: str = Field(default="manual", max_length=120)
    location: str = Field(default="", max_length=200)
    country: str = Field(default="", max_length=100)
    remote_status: str = Field(default="", max_length=20)
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = Field(default="", max_length=12)
    external_id: str = Field(default="", max_length=200)
    deadline: str = Field(default="", max_length=40)


class ScoreWeightsIn(BaseModel):
    weights: dict[str, float]


class SkillGapOut(BaseModel):
    skill: str
    matches: int = 0


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_url: str
    application_url: str
    company: str
    title: str
    description: str
    location: str
    country: str
    remote_status: str
    employment_type: str
    experience_level: str
    salary_min: float | None
    salary_max: float | None
    salary_currency: str
    skills: list
    requirements: list
    responsibilities: list
    benefits: list
    posted_at: datetime | None
    deadline: datetime | None
    discovered_at: datetime
    external_id: str
    status: str
    score: float | None
    score_band: str
    score_label: str
    score_breakdown: dict
    manual_override_score: float | None
    risk_level: str
    risk_flags: list
    analysis: dict
    matched_skills: list
    missing_skills: list
    matched_projects: list
    notes: str


class JobListOut(BaseModel):
    items: list[JobOut]
    total: int


class DuplicateOut(BaseModel):
    imported: bool
    duplicate: bool
    reason: str = ""
    job: JobOut | None = None


class AnalyzeOut(BaseModel):
    job: JobOut
    analysis: dict
    score: float | None = None
    score_band: str = ""
    score_label: str = ""


class JobSourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: str = Field(default="MANUAL", max_length=40)
    base_url: str = Field(default="", max_length=400)
    enabled: bool = True
    authentication_required: bool = False
    rate_limit: int = Field(default=0, ge=0)


class JobSourceOut(JobSourceIn):
    model_config = ConfigDict(from_attributes=True)

    id: int