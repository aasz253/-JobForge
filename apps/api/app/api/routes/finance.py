"""Financial goal tracking."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.finance import GoalIn, GoalOut, IncomeIn, IncomeRecordOut

from ...database import get_db
from ...models import IncomeRecord, User
from ..deps import get_current_user
from ...services.dashboard import financial_summary, get_active_goal

router = APIRouter(tags=["finance"])


@router.get("/financial-goal", response_model=GoalOut)
def get_goal(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return financial_summary(db, user.id)


@router.put("/financial-goal", response_model=GoalOut)
def update_goal(payload: GoalIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    goal = get_active_goal(db, user.id)
    goal.target_amount = payload.target_amount
    goal.currency = payload.currency
    if goal.started_at is None:
        goal.started_at = datetime.utcnow()
    db.commit()
    return financial_summary(db, user.id)


@router.get("/income", response_model=list[IncomeRecordOut])
def list_income(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[IncomeRecordOut]:
    return (
        db.query(IncomeRecord)
        .filter(IncomeRecord.user_id == user.id)
        .order_by(IncomeRecord.recorded_on.desc())
        .all()
    )


@router.post("/income", response_model=IncomeRecordOut, status_code=status.HTTP_201_CREATED)
def add_income(payload: IncomeIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> IncomeRecordOut:
    goal = get_active_goal(db, user.id)
    recorded_on = date.fromisoformat(payload.recorded_on) if payload.recorded_on else date.today()
    record = IncomeRecord(
        user_id=user.id,
        goal_id=goal.id,
        amount=payload.amount,
        currency=payload.currency,
        category=payload.category,
        description=payload.description,
        recorded_on=recorded_on,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/income/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(income_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    rec = db.query(IncomeRecord).filter(IncomeRecord.id == income_id, IncomeRecord.user_id == user.id).first()
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    db.delete(rec)
    db.commit()