"""User, sessions, candidate profile and per-user settings."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base_utils import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    profile: Mapped["CandidateProfile | None"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip: Mapped[str] = mapped_column(String(64), default="")

    user: Mapped["User"] = relationship(back_populates="sessions")


class CandidateProfile(TimestampMixin, Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    headline: Mapped[str] = mapped_column(String(300), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    linkedin: Mapped[str] = mapped_column(String(300), default="")
    github: Mapped[str] = mapped_column(String(300), default="")
    portfolio: Mapped[str] = mapped_column(String(300), default="")
    x_url: Mapped[str] = mapped_column(String(300), default="")
    youtube: Mapped[str] = mapped_column(String(300), default="")
    instagram: Mapped[str] = mapped_column(String(300), default="")
    other_links: Mapped[list] = mapped_column(JSON, default=list)

    availability: Mapped[str] = mapped_column(String(100), default="")
    work_authorization: Mapped[str] = mapped_column(String(300), default="")
    preferred_employment_type: Mapped[str] = mapped_column(String(64), default="FULL_TIME")
    preferred_locations: Mapped[list] = mapped_column(JSON, default=list)
    remote_preference: Mapped[bool] = mapped_column(Boolean, default=True)
    salary_expectation_min: Mapped[float | None] = mapped_column(nullable=True)
    salary_expectation_max: Mapped[float | None] = mapped_column(nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(12), default="KSh")
    notice_period_days: Mapped[int] = mapped_column(Integer, default=0)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    target_roles: Mapped[list] = mapped_column(JSON, default=list)
    target_industries: Mapped[list] = mapped_column(JSON, default=list)

    user: Mapped["User"] = relationship(back_populates="profile")


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(100))
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


# Unique constraint: (user_id, key)
from sqlalchemy import func, UniqueConstraint  # noqa: E402

__table_args_ = UniqueConstraint("user_id", "key", name="uq_settings_user_key")
Setting.__table_args__ = (__table_args_,)