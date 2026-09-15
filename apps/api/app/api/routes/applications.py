"""Applications: lifecycle, tracking, follow-ups, quality gate."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from jobforge_shared.constants import JobStatus
from app.schemas.applications import (
    ApplicationCreateIn,
    ApplicationOut,
    ApplicationUpdateIn,
    ConfirmSubmittedIn,
    FeedbacksIn,
    FollowupOut,
)

from ...database import get_db
from ...models import Application, Followup, User
from ..deps import get_current_user
from ...services.applications import (
    create_application,
    due_followups,
    list_applications,
    quality_check,
    update_application,
)
from datetime import datetime, timezone

router = APIRouter(tags=["applications"])


@router.get("/applications", response_model=list[ApplicationOut])
def get_applications(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ApplicationOut]:
    apps = list_applications(db, user.id, status=status_filter)
    return [ApplicationOut.model_validate(a) for a in apps]


@router.post("/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_app(payload: ApplicationCreateIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ApplicationOut:
    app = create_application(db, user.id, payload)
    if app is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create application.")
    return ApplicationOut.model_validate(app)


@router.get("/applications/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ApplicationOut:
    app = db.query(Application).filter(Application.id == application_id, Application.user_id == user.id).first()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    return ApplicationOut.model_validate(app)


@router.patch("/applications/{application_id}", response_model=ApplicationOut)
def update_app(
    application_id: int,
    payload: ApplicationUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApplicationOut:
    updates = payload.model_dump(exclude_unset=True)
    app, err = update_application(db, user.id, application_id, updates)
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err or "Not found.")
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    return ApplicationOut.model_validate(app)


@router.post("/applications/{application_id}/submit", response_model=ApplicationOut)
def mark_submitted(
    application_id: int,
    payload: ConfirmSubmittedIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApplicationOut:
    app, err = update_application(db, user.id, application_id, {"status": JobStatus.APPLIED}, confirmed=payload.confirmed)
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err or "Not found.")
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    return ApplicationOut.model_validate(app)


@router.post("/applications/{application_id}/quality-check")
def check_quality(application_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    result = quality_check(db, user.id, application_id)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


@router.get("/applications/{application_id}/followups", response_model=list[FollowupOut])
def application_followups(application_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[FollowupOut]:
    followups = (
        db.query(Followup)
        .filter(Followup.application_id == application_id, Followup.user_id == user.id)
        .order_by(Followup.day)
        .all()
    )
    return [FollowupOut.model_validate(f) for f in followups]


@router.get("/followups/due", response_model=list[FollowupOut])
def list_due_followups(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[FollowupOut]:
    return [FollowupOut.model_validate(f) for f in due_followups(db, user.id)]


@router.post("/followups/{followup_id}/complete", status_code=status.HTTP_200_OK)
def complete_followup(followup_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    fu = db.query(Followup).filter(Followup.id == followup_id, Followup.user_id == user.id).first()
    if fu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found.")
    fu.status = "DONE"
    fu.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Follow-up (day {fu.day}) marked as done."}


@router.post("/applications/{application_id}/feedback")
def record_feedback(application_id: int, payload: FeedbacksIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    app = db.query(Application).filter(Application.id == application_id, Application.user_id == user.id).first()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    existing = app.notes + "\n---\nFEEDBACK: " + " | ".join(payload.feedbacks[:20])
    app.notes = existing[-20_000:]
    db.commit()
    return {"message": "Feedback recorded.", "feedback_count": len(payload.feedbacks[:20])}