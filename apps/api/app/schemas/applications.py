"""Application, follow-up, finance schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from jobforge_shared.constants import (
    BOARD_COLUMN_MEMBERS,
    BOARD_COLUMNS,
    JobStatus,
)


class ApplicationCreateIn(BaseModel):
    job_id: int | None = None
    company: str = Field(default="", max_length=200)
    title: str = Field(default="", max_length=300)
    application_url: str = Field(default="", max_length=800)
    status: JobStatus = JobStatus.PREPARING
    notes: str = Field(default="", max_length=20_000)
    salary_entered: float | None = None
    required_documents: list[str] = Field(default_factory=list)


class ApplicationUpdateIn(BaseModel):
    status: JobStatus | None = None
    notes: str | None = Field(default=None, max_length=20_000)
    application_url: str | None = Field(default=None, max_length=800)
    cv_version_id: int | None = None
    salary_entered: float | None = None
    applied_at: datetime | None = None
    feedback: str | None = Field(default=None, max_length=20_000)
    answers: dict | None = None


class ConfirmSubmittedIn(BaseModel):
    confirmed: bool = True


class QualityCheckIn(BaseModel):
    confirmed: bool = True


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int | None
    status: str
    status_updated_at: datetime
    company: str
    title: str
    application_url: str
    deadline: datetime | None
    applied_at: datetime | None
    salary_entered: float | None
    notes: str
    required_documents: list
    answers: dict
    score_at_application: float | None
    matched_projects: list
    cv_used: str
    created_at: datetime
    updated_at: datetime


class FollowupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    day: int
    due_date: datetime
    status: str
    draft: str


class FeedbacksIn(BaseModel):
    feedbacks: list[str] = Field(default_factory=list)


class MissionTargets(BaseModel):
    jobs_discovered: int = 0
    jobs_qualified: int = 0
    applications: int = 0
    recruiter_connections: int = 0
    recruiter_messages: int = 0
    follow_ups: int = 0
    technical_content: int = 0


class MissionCounts(BaseModel):
    jobs_discovered: int = 0
    jobs_qualified: int = 0
    applications: int = 0
    recruiter_connections: int = 0
    recruiter_messages: int = 0
    follow_ups: int = 0
    technical_content: int = 0


class Mission(BaseModel):
    targets: MissionTargets = Field(default_factory=MissionTargets)
    counts: MissionCounts = Field(default_factory=MissionCounts)
    score: float = 0.0
    percent: float = 0.0


class MissionBreakdown(BaseModel):
    targets: dict[str, int] = Field(default_factory=dict)
    counts: dict[str, int] = Field(default_factory=dict)
    score: int = 0
    percent: float = 0.0


class MissionCounts(BaseModel):
    jobs_discovered: int = 0
    jobs_qualified: int = 0
    applications: int = 0
    followups: int = 0


class MissionBreakdown(BaseModel):
    targets: dict[str, int] = Field(default_factory=dict)
    counts: dict[str, int] = Field(default_factory=dict)
    score: int = 0
    percent: float = 0.0


class DashboardOut(BaseModel):
    jobs_discovered: int = 0
    qualified_jobs: int = 0
    applications_this_week: int = 0
    applications_this_month: int = 0
    interviews: int = 0
    technical_interviews: int = 0
    offers: int = 0
    accepted: int = 0
    response_rate: float = 0.0
    interview_rate: float = 0.0
    application_to_offer_rate: float = 0.0
    current_income: float = 0.0
    financial_goal_amount: float = 1_000_000
    financial_goal_currency: str = "KSh"
    financial_progress: float = 0.0
    top_jobs: list[dict] = Field(default_factory=list)
    mission: MissionBreakdown = Field(default_factory=MissionBreakdown)
    mission_progress: float = 0.0
    board: dict[str, int] = Field(default_factory=dict)
    due_followups: int = 0


class AnalyticsOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    totals: dict = Field(default_factory=dict)
    rates: dict = Field(default_factory=dict)
    by_source: list[dict] = Field(default_factory=list)
    by_status: list[dict] = Field(default_factory=list)
    by_score_band: list[dict] = Field(default_factory=list)
    by_week: list[dict] = Field(default_factory=list)
    funnel: dict = Field(default_factory=dict)
    bottlenecks: list[str] = Field(default_factory=list)


class GoalIn(BaseModel):
    target_amount: float = Field(default=1_000_000, gt=0)
    currency: str = Field(default="KSh", max_length=12)


class IncomeIn(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="KSh", max_length=12)
    category: str = Field(default="EMPLOYMENT", max_length=24)
    description: str = Field(default="", max_length=300)
    recorded_on: str | None = None


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_amount: float
    currency: str
    started_at: datetime | None
    total_earned: float = 0.0
    remaining: float = 0.0
    progress: float = 0.0
    monthly_income: float = 0.0