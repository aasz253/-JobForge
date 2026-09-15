"""Dashboard + analytics."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.applications import AnalyticsOut, DashboardOut

from ...database import get_db
from ...models import User
from ..deps import get_current_user
from ...services.dashboard import build_analytics, build_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return build_dashboard(db, user.id)


@router.get("/analytics", response_model=AnalyticsOut)
def analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return build_analytics(db, user.id)