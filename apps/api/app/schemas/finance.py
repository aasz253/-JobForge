from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class GoalIn(BaseModel):
    target_amount: float = Field(default=1_000_000, gt=0)
    currency: str = Field(default="KSh", max_length=12)


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_id: int = Field(validation_alias="goal_id")
    target_amount: float
    currency: str
    total_earned: float = Field(default=0.0, validation_alias="earned")
    remaining: float = 0.0
    progress: float = 0.0


class IncomeIn(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="KSh", max_length=12)
    category: str = Field(default="EMPLOYMENT", max_length=24)
    description: str = Field(default="", max_length=300)
    recorded_on: str = Field(default="", max_length=24)


class IncomeRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    currency: str
    category: str
    description: str
    recorded_on: date | None = None
    created_at: datetime
