"""Dashboard and analytics aggregation."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from jobforge_shared.constants import (
    BOARD_COLUMN_MEMBERS,
    DEFAULT_FINANCIAL_GOAL_AMOUNT,
    DEFAULT_FINANCIAL_GOAL_CURRENCY,
    DEFAULT_MISSION,
    JobStatus,
)

from ..models import (Application, FinancialGoal, Followup, IncomeRecord, Job)
from .applications import get_setting

INTERVIEW_STATUSES = {JobStatus.SCREENING.value, JobStatus.TECHNICAL_INTERVIEW.value, JobStatus.FINAL_INTERVIEW.value}
RESPONDED_STATUSES = INTERVIEW_STATUSES | {JobStatus.OFFER.value, JobStatus.ACCEPTED.value, JobStatus.REJECTED.value, JobStatus.APPLICATION_RECEIVED.value}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_week(dt: datetime) -> datetime:
    day = dt.weekday()
    return (dt - timedelta(days=day)).replace(hour=0, minute=0, second=0, microsecond=0)


def get_active_goal(db: Session, user_id: int) -> FinancialGoal:
    goal = db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id).first()
    if goal is None:
        goal = FinancialGoal(user_id=user_id, target_amount=DEFAULT_FINANCIAL_GOAL_AMOUNT, currency=DEFAULT_FINANCIAL_GOAL_CURRENCY)
        db.add(goal)
        db.commit()
        db.refresh(goal)
    return goal


def financial_summary(db: Session, user_id: int) -> dict:
    goal = get_active_goal(db, user_id)
    total = db.query(func.coalesce(func.sum(IncomeRecord.amount), 0.0)).filter(IncomeRecord.user_id == user_id).scalar() or 0.0
    progress = min(round(total / goal.target_amount * 100, 1), 100.0) if goal.target_amount else 0.0
    return {
        "goal_id": goal.id,
        "target_amount": goal.target_amount,
        "currency": goal.currency,
        "earned": round(total, 2),
        "remaining": round(max(goal.target_amount - total, 0.0), 2),
        "progress": progress,
    }


def _mission_targets(db: Session, user_id: int) -> dict:
    from jobforge_shared.constants import DEFAULT_MISSION

    stored = get_setting(db, user_id, "settings.mission", None)
    if isinstance(stored, dict) and stored:
        return {**DEFAULT_MISSION, **{k: int(v) for k, v in stored.items()}}
    return dict(DEFAULT_MISSION)


def mission_progress(db: Session, user_id: int) -> tuple[dict, float]:
    targets = _mission_targets(db, user_id)
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    jobs_discovered = db.query(Job).filter(Job.user_id == user_id, Job.discovered_at >= start).count()
    jobs_qualified = db.query(Job).filter(Job.user_id == user_id, Job.discovered_at >= start, Job.score >= 70).count()
    apps = db.query(Application).filter(Application.user_id == user_id, Application.created_at >= start).count()
    followups = db.query(Followup).filter(Followup.user_id == user_id, Followup.status == "DONE", Followup.updated_at >= start).count()
    counts = {
        "jobs_discovered": jobs_discovered,
        "jobs_qualified": jobs_qualified,
        "applications": apps,
        "follow_ups": followups,
    }
    progress = 0.0
    total_targets = 0
    for key, target in targets.items():
        total_targets += target
        done = min(counts.get(key, 0), target)
        progress += done
    pct = round(progress / total_targets * 100, 1) if total_targets else 0.0
    return {"targets": targets, "counts": counts, "score": round(progress, 1), "percent": pct}, pct


def board_counts(db: Session, user_id: int) -> dict[str, int]:
    statuses = [s for s in db.query(Application.status).filter(Application.user_id == user_id).all()]
    counter = Counter(s[0] for s in statuses)
    board: dict[str, int] = {}
    for column, members in BOARD_COLUMN_MEMBERS.items():
        board[column] = sum(counter.get(m, 0) for m in members)
    return board


def build_dashboard(db: Session, user_id: int) -> dict:
    now = _utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    jobs_total = db.query(Job).filter(Job.user_id == user_id).count()
    qualified = db.query(Job).filter(Job.user_id == user_id, Job.score >= 70).count()

    apps = db.query(Application).filter(Application.user_id == user_id).all()
    apps_total = len(apps)
    apps_week = sum(1 for a in apps if a.created_at >= week_ago)
    apps_month = sum(1 for a in apps if a.created_at >= month_ago)
    interviews = sum(1 for a in apps if a.status in INTERVIEW_STATUSES)
    tech_interviews = sum(1 for a in apps if a.status == JobStatus.TECHNICAL_INTERVIEW.value)
    offers = sum(1 for a in apps if a.status == JobStatus.OFFER.value)
    accepted = sum(1 for a in apps if a.status == JobStatus.ACCEPTED.value)
    responded = sum(1 for a in apps if a.status in RESPONDED_STATUSES)

    response_rate = round(responded / apps_total * 100, 1) if apps_total else 0.0
    interview_rate = round(interviews / apps_total * 100, 1) if apps_total else 0.0
    offer_rate = round(offers / apps_total * 100, 1) if apps_total else 0.0

    finance = financial_summary(db, user_id)
    top_jobs = [
        {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "remote_status": j.remote_status,
            "score": j.score,
            "band": j.score_band,
            "label": j.score_label,
            "application_url": j.application_url,
        }
        for j in db.query(Job)
        .filter(Job.user_id == user_id, Job.score.isnot(None))
        .order_by(Job.score.desc())
        .limit(10)
        .all()
    ]

    mission, mission_pct = mission_progress(db, user_id)
    due = db.query(Followup).filter(Followup.user_id == user_id, Followup.status == "PENDING", Followup.due_date <= now).count()

    return {
        "jobs_discovered": jobs_total,
        "qualified_jobs": qualified,
        "applications_this_week": apps_week,
        "applications_this_month": apps_month,
        "interviews": interviews,
        "technical_interviews": tech_interviews,
        "offers": offers,
        "accepted": accepted,
        "response_rate": response_rate,
        "interview_rate": interview_rate,
        "application_to_offer_rate": offer_rate,
        "current_income": finance["earned"],
        "financial_goal_amount": finance["target_amount"],
        "financial_goal_currency": finance["currency"],
        "financial_progress": finance["progress"],
        "top_jobs": top_jobs,
        "mission": mission,
        "mission_progress": mission_pct,
        "board": board_counts(db, user_id),
        "due_followups": due,
    }


def build_analytics(db: Session, user_id: int) -> dict:
    apps = db.query(Application).filter(Application.user_id == user_id).all()
    jobs = db.query(Job).filter(Job.user_id == user_id).all()
    apps_total = len(apps)

    by_status = [{"status": s, "count": c} for s, c in Counter(a.status for a in apps).most_common()]
    by_source = [{"source": s, "count": c} for s, c in Counter(a.company for a in apps).most_common(15)]

    score_bands = Counter()
    for j in jobs:
        score = j.manual_override_score if j.manual_override_score is not None else j.score
        if score is None:
            score_bands["UNSCORED"] += 1
        elif score >= 90:
            score_bands["90-100"] += 1
        elif score >= 80:
            score_bands["80-89"] += 1
        elif score >= 70:
            score_bands["70-79"] += 1
        elif score >= 60:
            score_bands["60-69"] += 1
        else:
            score_bands["<60"] += 1
    by_score_band = [{"band": b, "count": c} for b, c in score_bands.most_common()]

    by_week = []
    if apps:
        earliest = min(a.created_at for a in apps)
        weeks = int((_utcnow() - earliest).days / 7) + 1
        for w in range(weeks, -1, -1):
            start = _start_of_week(_utcnow()) - timedelta(weeks=w)
            weeks_end = start + timedelta(weeks=1)
            count = sum(1 for a in apps if start <= a.created_at < weeks_end)
            if count or w == 0:
                by_week.append({"week": start.date().isoformat(), "count": count})

    interviews = sum(1 for a in apps if a.status in INTERVIEW_STATUSES)
    offers = sum(1 for a in apps if a.status == JobStatus.OFFER.value)
    accepted = sum(1 for a in apps if a.status == JobStatus.ACCEPTED.value)
    responded = sum(1 for a in apps if a.status in RESPONDED_STATUSES)

    funnel = {
        "discovered": len(jobs),
        "qualified": sum(1 for j in jobs if (j.manual_override_score if j.manual_override_score is not None else j.score or 0) >= 70),
        "applied": sum(1 for a in apps if a.applied_at is not None),
        "responded": responded,
        "interviews": interviews,
        "final_interviews": sum(1 for a in apps if a.status in (JobStatus.FINAL_INTERVIEW.value, JobStatus.OFFER.value, JobStatus.ACCEPTED.value)),
        "offers": offers,
        "accepted": accepted,
    }

    bottlenecks: list[str] = []
    if funnel["applied"] >= 10:
        rr = funnel["responded"] / funnel["applied"] * 100
        if rr < 15:
            bottlenecks.append(f"Response rate is low ({rr:.0f}%). Review CV keyword matching and target roles with score ≥80.")
        ir = funnel["interviews"] / funnel["applied"] * 100
        if rr < 30 and ir < 10:
            bottlenecks.append("Consider strengthening project evidence and tailoring each application.")
    if funnel["discovered"] and funnel["qualified"] / funnel["discovered"] < 0.3:
        bottlenecks.append("A large share of discovered jobs never qualify — refine discovery keywords or sources.")
    if not bottlenecks and apps_total == 0:
        bottlenecks.append("No applications yet. Import jobs and start with a priority match.")

    totals = {
        "applications_total": apps_total,
        "applications_with_job": sum(1 for a in apps if a.job_id),
        "jobs_total": len(jobs),
        "avg_score": round(sum((j.score or 0) for j in jobs) / len(jobs), 1) if jobs else 0.0,
    }

    avg_times: dict = {}
    responded_apps = [a for a in apps if a.applied_at and a.status in RESPONDED_STATUSES]
    if responded_apps:
        days = [(a.status_updated_at - a.applied_at).days for a in responded_apps]
        avg_times["avg_days_to_response"] = round(sum(days) / len(days), 1)

    return {
        "totals": totals,
        "rates": {
            "response_rate": round(responded / apps_total * 100, 1) if apps_total else 0.0,
            "interview_rate": round(interviews / apps_total * 100, 1) if apps_total else 0.0,
            "offer_rate": round(offers / apps_total * 100, 1) if apps_total else 0.0,
            "accepted_rate": round(accepted / apps_total * 100, 1) if apps_total else 0.0,
            **avg_times,
        },
        "by_source": by_source,
        "by_status": by_status,
        "by_score_band": by_score_band,
        "by_week": by_week,
        "funnel": funnel,
        "bottlenecks": bottlenecks,
    }