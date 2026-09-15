"""Career evidence: skills, projects, CV documents, content drafts."""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base_utils import TimestampMixin


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")


class CandidateSkill(TimestampMixin, Base):
    __tablename__ = "candidate_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80), default="other")  # human group label
    proficiency: Mapped[str] = mapped_column(String(40), default="")  # Beginner/Intermediate/Advanced
    evidence: Mapped[str] = mapped_column(Text, default="")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    problem: Mapped[str] = mapped_column(Text, default="")
    solution: Mapped[str] = mapped_column(Text, default="")
    architecture: Mapped[str] = mapped_column(Text, default="")
    technologies: Mapped[list] = mapped_column(JSON, default=list)
    security: Mapped[list] = mapped_column(JSON, default=list)
    skills_demonstrated: Mapped[list] = mapped_column(JSON, default=list)
    key_achievements: Mapped[list] = mapped_column(JSON, default=list)
    github_url: Mapped[str] = mapped_column(String(400), default="")
    live_url: Mapped[str] = mapped_column(String(400), default="")
    demo_url: Mapped[str] = mapped_column(String(400), default="")
    deployment_url: Mapped[str] = mapped_column(String(400), default="")
    evidence_strength: Mapped[str] = mapped_column(String(20), default="medium")  # none/low/medium/strong
    source: Mapped[str] = mapped_column(String(30), default="manual")  # manual | github
    github_repo_id: Mapped[int | None] = mapped_column(nullable=True)
    is_fork: Mapped[bool] = mapped_column(Boolean, default=False)
    private: Mapped[bool] = mapped_column(Boolean, default=False)


class ProjectEvidence(TimestampMixin, Base):
    __tablename__ = "project_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(64))  # github, readme, pypi, demo, article, cert
    value: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(100), default="")

    project: Mapped["Project"] = relationship()


class CvDocument(TimestampMixin, Base):
    __tablename__ = "cv_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), default="Master CV")
    format: Mapped[str] = mapped_column(String(12), default="")  # pdf | docx
    content_text: Mapped[str] = mapped_column(Text, default="")
    source_hash: Mapped[str] = mapped_column(String(64), default="")


class CvVersion(TimestampMixin, Base):
    __tablename__ = "cv_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    cv_document_id: Mapped[int | None] = mapped_column(ForeignKey("cv_documents.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(120))  # e.g. "AI DevSecOps"
    content_text: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ContentDraft(TimestampMixin, Base):
    __tablename__ = "content_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40))  # linkedin_post, x_post, article, job_search_post...
    platform: Mapped[str] = mapped_column(String(30), default="linkedin")
    title: Mapped[str] = mapped_column(String(300), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    related_project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)