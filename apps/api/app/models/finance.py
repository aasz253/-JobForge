"""Financial goal tracking."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .base_utils import TimestampMixin


class FinancialGoal(TimestampMixin, Base):
    __tablename__ = "financial_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_amount: Mapped[float] = mapped_column(Float, default=1_000_000)
    currency: Mapped[str] = mapped_column(String(12), default="KSh")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Integer, default=1)


class IncomeRecord(TimestampMixin, Base):
    __tablename__ = "income_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("financial_goals.id", ondelete="SET NULL"), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(12), default="KSh")
    category: Mapped[str] = mapped_column(String(24), default="EMPLOYMENT")  # EMPLOYMENT|CONTRACT|FREELANCE|PRODUCT|OTHER
    description: Mapped[str] = mapped_column(String(300), default="")
    recorded_on: Mapped[date] = mapped_column(Date)