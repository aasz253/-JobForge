"""Seed demo data for a development user.

Usage:
    python -m app.scripts.seed_demo --email you@example.com --password 'a long passphrase'

Everything is explicitly *demo* data toggled by the caller. Sensitive values are
never hardcoded here.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app import crud
from app.core.security import hash_password  # noqa: F401
from app.database import SessionLocal, init_db
from app.models import (
    CandidateProfile,
    CandidateSkill,
    FinanceGoal,
    IncomeRecord,
    IncomeRecord as Record,
    Project,
    Setting,
    Skill,
    User,
)

from jobforge_shared.constants import DEFAULT_MISSION_VALUE

DEMO = {
    "email": "demo@sifunacodex.dev",
    "password": "correct-horse-battery-staple",
    "full_name": "Sifuna Codex",
    "profile": {
        "headline": "AI / DevSecOps / Cybersecurity Practitioner",
        "summary": (
            "Hands-on builder shipping DevSecOps and AI-security tooling. Public evidence:\n"
            "DeployForge (CI/CD + k8s + Terraform + SecretsGuard), PushForge (Git automation),\n"
            "SifunaCodex public repos, GitHub Actions + Bandit + Trivy pipelines."
        ),
    },
    "skills": [
        {"name": "Kubernetes", "category": "Containers", "proficiency": "Intermediate"},
        {"name": "Docker", "category": "Containers", "proficiency": "Intermediate"},
        {"name": "CI/CD", "category": "DevOps", "proficiency": "Advanced"},
        {"name": "GitHub Actions", "category": "DevOps", "proficiency": "Advanced"},
        {"name": "AWS", "category": "Cloud", "proficiency": "Intermediate"},
        {"name": "Python", "category": "Development", "proficiency": "Advanced"},
        {"name": "Terraform", "category": "Cloud", "proficiency": "Intermediate"},
        {"name": "Security scanning", "category": "Security", "proficiency": "Intermediate"},
        {"name": "OWASP", "category": "Security", "proficiency": "Intermediate"},
        {"name": "Git", "category": "DevOps", "proficiency": "Advanced"},
        {"name": "GitHub", "category": "DevOps", "proficiency": "Advanced"},
        {"name": "Linux", "category": "Systems", "proficiency": "Intermediate"},
    ],
    "projects": [
        {
            "name": "DeployForge",
            "slug": "deployforge",
            "description": "CI/CD + container orchestration toolkit.",
            "technologies": ["CI/CD", "Kubernetes", "Docker", "Terraform"],
            "skills_demonstrated": ["CI/CD", "Kubernetes", "Docker", "Terraform"],
            "github_url": "https://github.com/SifunaCodex/deployforge",
            "live_url": "",
        },
        {
            "name": "PushForge",
            "slug": "pushforge",
            "description": "Git automation workflow engine.",
            "technologies": ["Git", "GitHub", "Python"],
            "skills_demonstrated": ["Git", "GitHub", "Python"],
            "github_url": "https://github.com/SifunaCodex/pushforge",
            "live_url": "",
        },
        {
            "name": "SecretsGuard",
            "slug": "secretsguard",
            "description": "Secrets & API-key leak prevention for repos.",
            "technologies": ["Security", "GitHub Actions"],
            "skills_demonstrated": ["Security", "GitHub Actions"],
            "github_url": "https://github.com/SifunaCodex/secretsguard",
            "live_url": "",
        },
    ],
}


def seed(db: Session, *, reset: bool = True) -> User:
    email = DEMO["email"]
    if reset:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(DEMO["password"]),
            full_name=DEMO["full_name"],
        )
        db.add(user)
        db.flush()

    profile = CandidateProfile(user_id=user.id, **DEMO["profile"])
    db.add(profile)

    for s in DEMO["skills"]:
        db.add(CandidateSkill(user_id=user.id, **s))

    for p in DEMO["projects"]:
        db.add(Project(user_id=user.id, **p))

    goal = FinanceGoal(
        user_id=user.id,
        target_amount=1_000_000.0,
        currency="KSh",
        started_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    db.add(goal)
    db.flush()
    db.add_all(
        [
            IncomeRecord(
                user_id=user.id,
                goal_id=goal.id,
                amount=150_000.0,
                currency="KSh",
                category="EMPLOYMENT",
                recorded_on=date(2026, 4, 7),
            ),
            IncomeRecord(
                user_id=user.id,
                goal_id=goal.id,
                amount=90_000.0,
                currency="KSh",
                category="CONTRACT",
                recorded_on=date(2026, 5, 12),
            ),
        ]
    )
    db.add(Setting(user_id=user.id, key="mission", value=DEFAULT_MISSION_VALUE))
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the JobForge demo user.")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        if args.email:
            DEMO["email"] = args.email
        if args.password:
            DEMO["password"] = args.password
        seed(db, reset=not args.no_reset)
        print("Seeded demo user:", DEMO["email"])
    finally:
        db.close()


if __name__ == "__main__":
    main()