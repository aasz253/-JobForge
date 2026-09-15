"""Jobs: discovery, import, analysis, scoring, sources."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.ratelimit import limiter
from app.schemas.jobs import (
    AnalyzeOut,
    DuplicateOut,
    ImportManualIn,
    ImportUrlIn,
    JobListOut,
    JobOut,
    JobSourceIn,
    JobSourceOut,
    ScoreWeightsIn,
)

from ...database import get_db
from ...models import Job, JobSource
from ...models import User
from ..deps import get_current_user
from ...services.jobs import analyze_job, import_job_from_manual, import_job_from_url, list_jobs, reweight_scores

router = APIRouter(tags=["jobs"])


def _rate_limit_import(ip: str) -> None:
    s = get_settings()
    if not limiter.hit(f"import:{ip}", s.rate_limit_import, s.rate_limit_import_window):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Import rate limit reached. Try again later.")


@router.get("/jobs", response_model=JobListOut)
def get_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    min_score: float | None = Query(default=None, ge=0, le=100),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    items, total = list_jobs(db, user.id, status=status_filter, min_score=min_score, search=search, limit=limit, offset=offset)
    return {"items": [JobOut.model_validate(j) for j in items], "total": total}


@router.get("/jobs/top", response_model=list[JobOut])
def top_jobs(
    min_score: float = Query(default=60, ge=0, le=100),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[JobOut]:
    jobs = (
        db.query(Job)
        .filter(Job.user_id == user.id, Job.score.isnot(None))
        .order_by(Job.score.desc())
        .limit(limit)
        .all()
    )
    return [JobOut.model_validate(j) for j in jobs]


@router.post("/jobs/import-url", response_model=DuplicateOut)
def import_url(payload: ImportUrlIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    ip = request.client.host if request.client else "unknown"
    _rate_limit_import(ip)
    result = import_job_from_url(db, user.id, payload.url, ip=ip)
    if "error" in result and not result.get("imported"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result["error"])
    job = result.get("job")
    if job:
        analyze_job(db, user.id, job.id)  # score + analyze immediately
    return {
        "imported": result["imported"],
        "duplicate": result.get("duplicate", False),
        "reason": result.get("reason", ""),
        "job": JobOut.model_validate(db.query(Job).get(job.id)) if job else None,
    }


@router.post("/jobs/import", response_model=DuplicateOut, status_code=status.HTTP_201_CREATED)
def import_manual(payload: ImportManualIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    ip = request.client.host if request.client else "unknown"
    _rate_limit_import(ip)
    result = import_job_from_manual(db, user.id, payload.model_dump(), ip=ip)
    job = result.get("job")
    if job:
        analyze_job(db, user.id, job.id)
    return {
        "imported": result["imported"],
        "duplicate": result.get("duplicate", False),
        "reason": result.get("reason", ""),
        "job": JobOut.model_validate(db.query(Job).get(job.id)) if job else None,
    }


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Job:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user.id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


@router.post("/jobs/{job_id}/analyze", response_model=AnalyzeOut)
def analyze(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user.id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    analyze_job(db, user.id, job_id)
    db.refresh(job)
    return {
        "job": JobOut.model_validate(job),
        "analysis": job.analysis,
        "score": job.score,
        "score_band": job.score_band,
        "score_label": job.score_label,
    }


@router.post("/jobs/score/reweight")
def rescore_all(payload: ScoreWeightsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    updated, ids = reweight_scores(db, user.id, payload.weights)
    return {"message": f"Re-scored {updated} jobs.", "updated": updated, "ids": ids[:200]}


@router.post("/jobs/{job_id}/override", response_model=JobOut)
def override_score(job_id: int, score: ScoreWeightsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Job:
    """Manually override a job's score (score.weights holds the override value)."""
    if score.weights.get("manual", None) is not None:
        value = float(score.weights["manual"])
        if not (0 <= value <= 100):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Score must be 0-100.")
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == user.id).first()
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
        job.manual_override_score = value
        db.commit()
        db.refresh(job)
        return job
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Provide {"weights": {"manual": 85}}.')


# ---------------------------------------------------------------------------
# Job sources
# ---------------------------------------------------------------------------


@router.get("/job-sources", response_model=list[JobSourceOut])
def list_sources(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[JobSource]:
    return db.query(JobSource).filter(JobSource.user_id == user.id).all()


@router.post("/job-sources", response_model=JobSourceOut, status_code=status.HTTP_201_CREATED)
def create_source(payload: JobSourceIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> JobSource:
    source = JobSource(user_id=user.id, **payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.patch("/job-sources/{source_id}", response_model=JobSourceOut)
def update_source(source_id: int, payload: JobSourceIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> JobSource:
    source = db.query(JobSource).filter(JobSource.id == source_id, JobSource.user_id == user.id).first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found.")
    for field, value in payload.model_dump().items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/job-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    source = db.query(JobSource).filter(JobSource.id == source_id, JobSource.user_id == user.id).first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found.")
    db.delete(source)
    db.commit()