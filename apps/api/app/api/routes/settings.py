"""Per-user application settings.

Privacy-related settings (e.g. the human approval gate, mission targets,
follow-up schedule, scoring weights) live here and are user-editable.
"""

from __future__ import annotations

from datetime import datetime, timezone

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from jobforge_shared.constants import DEFAULT_FOLLOWUP_SCHEDULE, DEFAULT_MISSION, DEFAULT_SCORE_WEIGHTS
from app.schemas.common import SettingsIn

from ...database import get_db
from ...models import Setting, User
from ..deps import get_current_user
from ...services.applications import get_setting

router = APIRouter(tags=["settings"])

_DEFAULTS = {
    "settings.approval": True,
    "settings.mission": DEFAULT_MISSION,
    "settings.followup_schedule": DEFAULT_FOLLOWUP_SCHEDULE,
    "settings.score_weights": DEFAULT_SCORE_WEIGHTS,
    "settings.financial_goal": {"amount": 1_000_000, "currency": "KSh"},
}


def _raw_settings(db: Session, user_id: int) -> dict:
    rows = db.query(Setting).filter(Setting.user_id == user_id).all()
    merged = {k: v for k, v in _DEFAULTS.items()}
    for row in rows:
        merged[row.key] = row.value
    return {k.replace("settings.", ""): v for k, v in merged.items()}


@router.get("/settings")
def get_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return _raw_settings(db, user.id)


@router.put("/settings")
def save_settings(payload: SettingsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    data = payload.model_dump(exclude_unset=True, exclude_none=True)

    mapping = {
        "require_approval_before_external_submission": ("settings.approval", None),
        "mission": ("settings.mission", "validate_mission"),
        "followup_schedule_days": ("settings.followup_schedule", None),
        "score_weights": ("settings.score_weights", "validate_weights"),
        "financial_goal_amount": ("settings.financial_goal", "merge_amount"),
        "financial_goal_currency": ("settings.financial_goal", "merge_currency"),
    }

    for field, value in data.items():
        if field not in mapping:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown setting: {field}")
        key, validator = mapping[field]
        if validator == "validate_mission":
            try:
                value = SettingsIn.validate_mission(value)
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        if validator == "validate_weights":
            value = validate_weights(value)
        if validator in ("merge_amount", "merge_currency"):
            current = get_setting(db, user.id, key, _DEFAULTS[key])
            merged = dict(current)
            merged["amount" if validator == "merge_amount" else "currency"] = value
            value = merged
        if validator == "validate_weights":
            # weights must be close to 100 in total; engine normalizes anyway
            total = sum(value.values())
            if abs(total - 100.0) > 25.0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scoring weights should total ~100.")

        row = db.query(Setting).filter(Setting.user_id == user.id, Setting.key == key).first()
        if row is None:
            row = Setting(user_id=user.id, key=key, value=value)
            db.add(row)
        else:
            row.value = value
        row.updated_at = datetime.now(timezone.utc)
    db.commit()
    record(db, user_id=user.id, action="settings.updated")
    return _raw_settings(db, user.id)


def validate_weights(value: dict) -> dict:
    allowed = set(DEFAULT_SCORE_WEIGHTS.keys())
    unknown = set(value) - allowed
    if unknown:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown weight keys: {sorted(unknown)}")
    return {k: float(v) for k, v in value.items()}