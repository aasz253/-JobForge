"""Candidate profile helpers: build the AI context from the database."""

from __future__ import annotations

from sqlalchemy.orm import Session

from jf_ai.analyzer import CandidateContext
from jf_scoring.engine import CandidateSkill, ProjectEvidence

from ..models import CandidateProfile, CandidateSkill as SkillModel, Project


def get_or_create_profile(db: Session, user_id: int) -> CandidateProfile:
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if profile is None:
        profile = CandidateProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def list_skills(db: Session, user_id: int) -> list[SkillModel]:
    return (
        db.query(SkillModel)
        .filter(SkillModel.user_id == user_id)
        .order_by(SkillModel.id)
        .all()
    )


def list_projects(db: Session, user_id: int) -> list[Project]:
    return db.query(Project).filter(Project.user_id == user_id).order_by(Project.id).all()


def build_candidate_context(db: Session, user_id: int) -> CandidateContext:
    """Assemble the evidence-bound candidate context used by AI + scoring.

    Only data that exists in the database is used — nothing is invented.
    """
    profile = get_or_create_profile(db, user_id)
    skills = [
        CandidateSkill(name=s.name, category=s.category, proficiency=s.proficiency, evidence=s.evidence)
        for s in list_skills(db, user_id)
    ]
    projects = [
        ProjectEvidence(
            name=p.name,
            skills=list(p.skills_demonstrated or []) + list(p.technologies or []),
            description=p.description or "",
        )
        for p in list_projects(db, user_id)
    ]
    return CandidateContext(
        profile_summary=profile.summary or "",
        headline=profile.headline or "",
        years_experience=profile.years_experience or 0,
        preferred_remote=bool(profile.remote_preference),
        skills=skills,
        projects=projects,
    )