"""Application lifecycle: create, track, follow-ups, quality gate.

The human-in-the-loop gate lives here: moving an application to APPLIED (i.e.
marking an externally-submitted application) requires an explicit confirmation
flag from the user. JobForge itself never performs the external submission.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from jobforge_shared.constants import DEFAULT_FOLLOWUP_SCHEDULE, JobStatus

from ..core.audit import record
from ..models import Application, CandidateProfile, Followup, Job, Setting
from .candidate import get_or_create_profile


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_setting(db: Session, user_id: int, key: str, default):
    row = db.query(Setting).filter(Setting.user_id == user_id, Setting.key == key).first()
    if row is None:
        return default
    return row.value


def approval_required(db: Session, user_id: int) -> bool:
    value = get_setting(db, user_id, "settings.approval", None)
    if value is None:
        return True
    return bool(value)


def create_application(db: Session, user_id: int, payload, ip: str = "") -> Application | None:
    job = None
    if payload.job_id:
        job = db.query(Job).filter(Job.id == payload.job_id, Job.user_id == user_id).first()
    if job is None:
        # application without a job row is allowed (manual tracking)
        pass

    app = Application(
        user_id=user_id,
        job_id=job.id if job else None,
        status=payload.status.value if hasattr(payload.status, "value") else str(payload.status),
        status_updated_at=_utcnow(),
        company=payload.company or (job.company if job else ""),
        title=payload.title or (job.title if job else ""),
        application_url=payload.application_url or (job.application_url if job else ""),
        notes=payload.notes or "",
        salary_entered=payload.salary_entered,
        required_documents=list(payload.required_documents or []),
    )
    if job is not None:
        app.score_at_application = job.score
        app.matched_projects = list(job.matched_projects or [])
    db.add(app)
    db.commit()
    db.refresh(app)
    record(db, user_id=user_id, action="application.created", entity_type="application", entity_id=app.id, ip=ip, detail=f"company={app.company}")
    return app


def update_application(
    db: Session,
    user_id: int,
    application_id: int,
    updates: dict,
    *,
    confirmed: bool = False,
    ip: str = "",
) -> tuple[Application | None, str | None]:
    """Apply updates. Returns (application, error_message)."""
    app = db.query(Application).filter(Application.id == application_id, Application.user_id == user_id).first()
    if app is None:
        return None, "Application not found"

    for field in ("notes", "application_url", "salary_entered", "answers", "feedback", "cv_version_id", "applied_at"):
        if field in updates:
            value = updates[field]
            if field == "cv_version_id" and value is not None:
                value = int(value)
            setattr(app, field, value)

    if "status" in updates and updates["status"] is not None:
        new_status = updates["status"]
        if hasattr(new_status, "value"):
            new_status = new_status.value
        if new_status == JobStatus.APPLIED.value:
            old = app.status
            # The human gate: without explicit confirmation, block marking as submitted.
            approval = approval_required(db, user_id)
            if approval and not confirmed:
                return app, "External submission requires explicit user confirmation."
            if old != JobStatus.APPLIED.value:
                app.applied_at = app.applied_at or _utcnow()
                schedule_followups(db, user_id, app)
                record(db, user_id=user_id, action="application.submitted", entity_type="application", entity_id=app.id, ip=ip, outcome="OK")
        app.status = new_status
        app.status_updated_at = _utcnow()

    db.commit()
    db.refresh(app)
    record(db, user_id=user_id, action="application.updated", entity_type="application", entity_id=app.id, ip=ip)
    return app, None


def schedule_followups(db: Session, user_id: int, app: Application) -> None:
    schedule = list(get_setting(db, user_id, "settings.followup_schedule", DEFAULT_FOLLOWUP_SCHEDULE))
    existing = {f.day for f in db.query(Followup).filter(Followup.application_id == app.id).all()}
    for day in schedule:
        if day in existing:
            continue
        due = _utcnow() + timedelta(days=day)
        db.add(
            Followup(
                user_id=user_id,
                application_id=app.id,
                day=day,
                due_date=due,
                status="PENDING",
                draft=build_followup_draft(app.company, app.title, day),
            )
        )


def build_followup_draft(company: str, role: str, day: int) -> str:
    if day <= 5:
        tone = "brief, warm status check"
    elif day <= 10:
        tone = "polite nudge referencing the timeline"
    else:
        tone = "final check-in before moving on"
    return (
        f"DRAFT (day {day}) — {tone}.\n"
        f"Subject: Following up on {role} at {company}\n"
        f"Hi {company or 'team'} team, I applied for the {role} role on ... and wanted to "
        f"check on the status. Happy to provide any further information. Thank you."
    )


def quality_check(db: Session, user_id: int, application_id: int) -> dict:
    """Application accuracy/security checklist before external submission."""
    app = db.query(Application).filter(Application.id == application_id, Application.user_id == user_id).first()
    if app is None:
        return {"ok": False, "error": "Application not found"}
    profile: CandidateProfile | None = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()

    checks: list[dict] = []
    def item(label: str, ok: bool, note: str = "") -> None:
        checks.append({"label": label, "ok": ok, "note": note})

    item("Name available", bool(profile and profile.headline), "Set your headline in Profile." if not (profile and profile.headline) else "")
    email_ok = bool(profile and profile.email)
    item("Contact email available", email_ok, "Add your contact email in Profile." if not email_ok else "")
    phone_ok = bool(profile and profile.phone)
    item("Phone available", phone_ok, "Add phone in Profile." if not phone_ok else "")
    cv_ok = False
    cv_name = ""
    if app.cv_version_id:
        from ..models import CvVersion

        cv = db.query(CvVersion).filter(CvVersion.id == app.cv_version_id, CvVersion.user_id == user_id).first()
        cv_ok = bool(cv and cv.content_text)
        cv_name = cv.name if cv else ""
    item("CV attached", cv_ok, "Attach a CV version to the application." if not cv_ok else f"Using: {cv_name}")
    job = db.query(Job).filter(Job.id == app.job_id).first() if app.job_id else None
    item("Application URL present", bool(app.application_url), "Set the application URL.")
    if job:
        unsupported = (job.analysis or {}).get("unsupported_claims") or []
        item("No fabricated experience detected", not unsupported, f"Unsupported claims: {unsupported}" if unsupported else "AI analysis found no unsupported claims.")
        item("Cover letter reviewed", True, "Review the AI draft in Application Workspace.")
        item("Work authorization / location reviewed", bool(profile and profile.work_authorization), "Add work authorization in Profile.")
    item("Answers reviewed for required questions", True, "Review every AI-generated answer before submission.")

    ready = all(c["ok"] for c in checks) and bool(app.application_url)
    return {"ok": ready, "checks": checks, "ready_to_submit": ready}


def list_applications(db: Session, user_id: int, status: str | None = None) -> list[Application]:
    query = db.query(Application).filter(Application.user_id == user_id)
    if status:
        query = query.filter(Application.status == status)
    return query.order_by(Application.updated_at.desc()).all()


def due_followups(db: Session, user_id: int) -> list[Followup]:
    today = _utcnow().date()
    return (
        db.query(Followup)
        .filter(Followup.user_id == user_id, Followup.status == "PENDING", Followup.due_date <= _utcnow())
        .order_by(Followup.due_date)
        .all()
    )