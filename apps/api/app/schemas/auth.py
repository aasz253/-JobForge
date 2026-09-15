from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from jobforge_shared.constants import ExperienceLevel, JobStatus, RemoteStatus


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=256)
    full_name: str = Field(default="", max_length=200)


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=256)


# ---------------------------------------------------------------------------
# Candidate profile
# ---------------------------------------------------------------------------


class ProfileIn(BaseModel):
    headline: str = Field(default="", max_length=300)
    summary: str = Field(default="", max_length=60_000)
    email: EmailStr | str = Field(default="")
    phone: str = Field(default="", max_length=64)
    country: str = Field(default="", max_length=120)
    city: str = Field(default="", max_length=120)
    years_experience: int = Field(default=0, ge=0, le=80)
    linkedin: str = Field(default="", max_length=400)
    github: str = Field(default="", max_length=400)
    portfolio: str = Field(default="", max_length=400)
    other_links: list[str] = Field(default_factory=list)
    availability: str = Field(default="", max_length=120)
    work_authorization: str = Field(default="", max_length=300)
    preferred_employment_type: str = Field(default="FULL_TIME", max_length=64)
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: bool = True
    salary_expectation_min: float | None = Field(default=None, ge=0)
    salary_expectation_max: float | None = Field(default=None, ge=0)
    salary_currency: str = Field(default="KSh", max_length=12)
    notice_period_days: int = Field(default=0, ge=0, le=365)


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="other", max_length=80)
    proficiency: str = Field(default="", max_length=40)
    evidence: str = Field(default="", max_length=4000)


class SkillOut(SkillIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(default="", max_length=220)
    description: str = Field(default="", max_length=20_000)
    problem: str = Field(default="", max_length=10_000)
    solution: str = Field(default="", max_length=10_000)
    architecture: str = Field(default="", max_length=10_000)
    technologies: list[str] = Field(default_factory=list)
    security: list[str] = Field(default_factory=list)
    skills_demonstrated: list[str] = Field(default_factory=list)
    github_url: str = Field(default="", max_length=400)
    live_url: str = Field(default="", max_length=400)


class ProjectOut(ProjectIn):
    model_config = ConfigDict(from_attributes=True)

    id: int