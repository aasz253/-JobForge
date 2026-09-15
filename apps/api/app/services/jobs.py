"""Job import, dedup, normalization, analysis and scoring service."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.audit import record
from jf_ai.analyzer import JobAnalysis, JobContext, get_analyzer
from jf_job_sources.base import NormalizedJob
from jf_job_sources.dedup import check_duplicate
from jf_job_sources.importer import import_from_manual_paste, import_from_url
from jf_scoring.engine import ScoringEngine

from ..models import Job
from .candidate import build_candidate_context


def _normalized_to_model(job: NormalizedJob, user_id: int) -> Job:
    model = Job(
        user_id=user_id,
        source=job.source or "manual",
        source_url=job.source_url or "",
        application_url=job.application_url or "",
        company=job.company,
        title=job.title,
        description=job.description,
        location=job.location or "",
        country=job.country or "",
        remote_status=job.remote_status.value if hasattr(job.remote_status, "value") else str(job.remote_status),
        employment_type=job.employment_type.value if hasattr(job.employment_type, "value") else str(job.employment_type),
        experience_level=job.experience_level.value if hasattr(job.experience_level, "value") else str(job.experience_level),
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency or "",
        skills=list(job.skills or []),
        requirements=list(job.requirements or []),
        responsibilities=list(job.responsibilities or []),
        benefits=list(job.benefits or []),
        posted_at=job.posted_at,
        deadline=job.deadline,
        discovered_at=job.discovered_at or datetime.utcnow(),
        external_id=job.external_id or "",
        content_hash=job.hash or "",
        status="DISCOVERED",
    )
    return model


def _to_job_context(model: Job) -> JobContext:
    return JobContext(
        title=model.title,
        company=model.company,
        description=model.description,
        location=model.location,
        remote_status=model.remote_status,
        salary_min=model.salary_min,
        salary_max=model.salary_max,
        salary_currency=model.salary_currency,
        url=model.source_url,
    )


def apply_analysis(db: Session, job: Job, weights: dict | None = None) -> JobAnalysis | None:
    """Run analysis + scoring and persist it onto the job."""
    settings = get_settings()
    candidate = build_candidate_context(db, job.user_id)
    analyzer = get_analyzer(
        settings.ai_provider,
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key,
        model=settings.ai_model,
        weights=weights,
    )
    analysis: JobAnalysis = analyzer.analyze(_to_job_context(job), candidate)

    score = getattr(analysis, "score", None)
    # rule-based path attaches no score; recompute for the persisted score fields
    engine = ScoringEngine(weights)
    result = engine.compute(
        job_text=job.description,
        candidate_skills=candidate.skills,
        projects=candidate.projects,
        candidate_years_experience=candidate.years_experience,
        candidate_prefers_remote=candidate.preferred_remote,
    )
    job.score = result.total
    job.score_band = result.band
    job.score_label = result.label
    job.score_breakdown = result.by_category
    job.matched_skills = result.matched_skills
    job.missing_skills = result.missing_skills
    job.matched_projects = result.matched_projects
    job.risk_level = analysis.risk_level
    job.risk_flags = analysis.risk_flags
    job.analysis = {
        "summary": analysis.summary,
        "required_skills": analysis.required_skills,
        "preferred_skills": analysis.preferred_skills,
        "experience_requirement": analysis.experience_requirement,
        "application_strategy": analysis.application_strategy,
        "risks": analysis.risks,
        "source": analysis.source,
        "unsupported_claims": analysis.unsupported_claims,
        "matched_skills_generated_at": datetime.utcnow().isoformat(),
    }
    db.commit()
    db.refresh(job)
    return analysis


def import_job_from_url(db: Session, user_id: int, url: str, ip: str = "") -> dict:
    """Import a single job from a URL. Returns an import result dict."""
    result = import_from_url(url)
    if not result.ok:
        record(db, user_id=user_id, action="job.import_url_failed", ip=ip, detail=result.error[:200])
        return {"imported": False, "duplicate": False, "error": result.error, "warnings": result.warnings}

    job = _normalized_to_model(result.job, user_id)
    job.content_hash = result.job.hash or compute_hash_for(result.job)
    return _persist_job(db, user_id, job, ip=ip)


def compute_hash_for(normalized: NormalizedJob) -> str:
    from jf_job_sources.dedup import compute_content_hash

    return compute_content_hash(normalized)


def import_job_from_manual(db: Session, user_id: int, payload: dict, ip: str = "") -> dict:
    normalized = import_from_manual_paste(payload)
    normalized.hash = compute_hash_for(normalized)
    job = _normalized_to_model(normalized, user_id)
    return _persist_job(db, user_id, job, ip=ip)


def _persist_job(db: Session, user_id: int, job: Job, ip: str) -> dict:
    existing = (
        db.query(Job)
        .filter(Job.user_id == user_id, Job.content_hash == job.content_hash)
        .first()
    )
    if existing is None and job.content_hash == "":
        existing = (
            db.query(Job)
            .filter(Job.user_id == user_id, Job.external_id == job.external_id, Job.external_id != "")
            .first()
        )

    if existing is not None:
        # Duplicate detected — merge fresh metadata instead of creating a second job.
        for field in ("description", "requirements", "responsibilities", "benefits", "salary_min", "salary_max", "salary_currency", "deadline"):
            incoming = getattr(job, field)
            if incoming:
                setattr(existing, field, incoming)
        record(db, user_id=user_id, action="job.duplicate_merged", entity_type="job", entity_id=existing.id, ip=ip)
        db.commit()
        db.refresh(existing)
        return {"imported": True, "duplicate": True, "reason": "Duplicate detected — existing job updated.", "job": existing}

    db.add(job)
    db.commit()
    db.refresh(job)
    record(db, user_id=user_id, action="job.imported", entity_type="job", entity_id=job.id, ip=ip)
    return {"imported": True, "duplicate": False, "job": job}


def analyze_job(db: Session, user_id: int, job_id: int, weights: dict | None = None) -> Job | None:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    if job is None:
        return None
    apply_analysis(db, job, weights=weights)
    return job


def list_jobs(
    db: Session,
    user_id: int,
    *,
    status: str | None = None,
    min_score: float | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[Job], int]:
    query = db.query(Job).filter(Job.user_id == user_id)
    if status:
        query = query.filter(Job.status == status)
    if min_score is not None:
        query = query.filter(Job.score >= min_score)
    if search:
        like = f"%{search}%"
        query = query.filter(Job.title.ilike(like) | Job.company.ilike(like))
    total = query.count()
    items = query.order_by(Job.score.desc().nullslast()).offset(offset).limit(limit).all()
    return items, total


def reweight_scores(db: Session, user_id: int, weights: dict) -> tuple[int, list[int]]:
    """Re-score every job with new weights. Returns (updated_count, ids)."""
    jobs = db.query(Job).filter(Job.user_id == user_id).all()
    engine = ScoringEngine(weights)
    candidate = build_candidate_context(db, user_id)
    updated: list[int] = []
    for job in jobs:
        result = engine.compute(
            job_text=job.description,
            candidate_skills=candidate.skills,
            projects=candidate.projects,
            candidate_years_experience=candidate.years_experience,
            candidate_prefers_remote=candidate.preferred_remote,
        )
        job.score = result.total
        job.score_band = result.band
        job.score_label = result.label
        job.score_breakdown = result.by_category
        job.matched_skills = result.matched_skills
        job.missing_skills = result.missing_skills
        job.matched_projects = result.matched_projects
        updated.append(job.id)
    db.commit()
    return len(updated), updated