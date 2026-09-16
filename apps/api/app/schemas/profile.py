"""Candidate profile, skills and project schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileIn(BaseModel):
    headline: str = Field(default="", max_length=300)
    summary: str = Field(default="", max_length=20_000)
    email: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=64)
    country: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    linkedin: str = Field(default="", max_length=300)
    github: str = Field(default="", max_length=300)
    portfolio: str = Field(default="", max_length=300)
    x_url: str = Field(default="", max_length=300)
    youtube: str = Field(default="", max_length=300)
    instagram: str = Field(default="", max_length=300)
    other_links: list[str] = Field(default_factory=list)
    availability: str = Field(default="", max_length=100)
    work_authorization: str = Field(default="", max_length=300)
    preferred_employment_type: str = Field(default="FULL_TIME", max_length=64)
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: bool = True
    salary_expectation_min: float | None = None
    salary_expectation_max: float | None = None
    salary_currency: str = Field(default="KSh", max_length=12)
    notice_period_days: int = Field(default=0, ge=0, le=365)
    years_experience: int = Field(default=0, ge=0, le=80)
    target_roles: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ProfileUpdateIn(ProfileIn):
    """PUT body: accepts the display name too (handled separately on User)."""

    full_name: str = Field(default="", max_length=200)


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="other", max_length=80)
    proficiency: str = Field(default="", max_length=40)
    evidence: str = Field(default="", max_length=4000)


class SkillOut(SkillIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=20_000)
    problem: str = Field(default="", max_length=10_000)
    solution: str = Field(default="", max_length=10_000)
    architecture: str = Field(default="", max_length=10_000)
    technologies: list[str] = Field(default_factory=list)
    security: list[str] = Field(default_factory=list)
    skills_demonstrated: list[str] = Field(default_factory=list)
    key_achievements: list[str] = Field(default_factory=list)
    github_url: str = Field(default="", max_length=400)
    live_url: str = Field(default="", max_length=400)
    demo_url: str = Field(default="", max_length=400)
    deployment_url: str = Field(default="", max_length=400)
    evidence_strength: str = Field(default="medium", max_length=20)


class ProjectOut(ProjectIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    source: str
    created_at: datetime
    updated_at: datetime