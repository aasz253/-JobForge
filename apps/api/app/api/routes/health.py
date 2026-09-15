"""Health / meta."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.schemas.common import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    s = get_settings()
    return HealthOut(app=s.app_name, ai_provider=s.ai_provider)