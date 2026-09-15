"""Shared/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MessageOut(BaseModel):
    message: str
    detail: str = ""


class HealthOut(BaseModel):
    status: str = "ok"
    app: str = "JOBFORGE"
    version: str = "0.1.0"
    made_by: str = "Sifuna Codex"
    ai_provider: str = "none"


class SettingsIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    require_approval_before_external_submission: bool | None = Field(default=None, description="Human gate for external submission")
    mission: dict[str, int] | None = Field(default=None, description="Daily mission targets")
    followup_schedule_days: list[int] | None = Field(default=None, description="Follow-up days after submission")
    score_weights: dict[str, float] | None = Field(default=None, description="Job scoring weights (should total 100)")
    financial_goal_amount: float | None = Field(default=None)
    financial_goal_currency: str | None = Field(default=None)

    @classmethod
    def validate_mission(cls, value: dict) -> dict:
        allowed = {"jobs_discovered", "jobs_qualified", "applications", "recruiter_connections", "recruiter_messages", "follow_ups", "technical_content"}
        bad = set(value) - allowed
        if bad:
            raise ValueError(f"Unknown mission keys: {', '.join(sorted(bad))}")
        return {k: int(v) for k, v in value.items() if k in allowed}