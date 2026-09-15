"""Candidate profile, skills, projects, CV upload, GitHub sync."""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.audit import record
from app.schemas.profile import ProfileIn, ProfileOut, ProjectIn, ProjectOut, SkillIn, SkillOut

from ...database import get_db
from ...models import CandidateProfile, CandidateSkill, CvDocument, Project
from ...models import User
from ..deps import get_current_user
from ...services.candidate import get_or_create_profile
from jf_cv.parser import parse_cv

router = APIRouter(tags=["profile"])


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CandidateProfile:
    return get_or_create_profile(db, user.id)


@router.put("/profile", response_model=ProfileOut)
def update_profile(payload: ProfileIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CandidateProfile:
    profile = get_or_create_profile(db, user.id)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    record(db, user_id=user.id, action="profile.updated", entity_type="profile", entity_id=profile.id)
    return profile


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@router.get("/skills", response_model=list[SkillOut])
def list_user_skills(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[CandidateSkill]:
    return db.query(CandidateSkill).filter(CandidateSkill.user_id == user.id).order_by(CandidateSkill.id).all()


@router.post("/skills", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def add_skill(payload: SkillIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CandidateSkill:
    exists = db.query(CandidateSkill).filter(CandidateSkill.user_id == user.id, CandidateSkill.name == payload.name.strip()).first()
    if exists:
        return exists
    skill = CandidateSkill(user_id=user.id, name=payload.name.strip(), category=payload.category, proficiency=payload.proficiency, evidence=payload.evidence)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    record(db, user_id=user.id, action="profile.skill_added", entity_type="skill", entity_id=skill.id)
    return skill


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    skill = db.query(CandidateSkill).filter(CandidateSkill.id == skill_id, CandidateSkill.user_id == user.id).first()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
    db.delete(skill)
    db.commit()
    record(db, user_id=user.id, action="profile.skill_removed", entity_type="skill", entity_id=skill_id)


# ---------------------------------------------------------------------------
# Projects (evidence engine)
# ---------------------------------------------------------------------------


def _slugify(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")[:220]


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Project]:
    return db.query(Project).filter(Project.user_id == user.id).order_by(Project.updated_at.desc()).all()


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Project:
    project = Project(user_id=user.id, **payload.model_dump(), slug=_slugify(payload.name))
    db.add(project)
    db.commit()
    db.refresh(project)
    record(db, user_id=user.id, action="project.created", entity_type="project", entity_id=project.id)
    return project


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    for field, value in payload.model_dump().items():
        setattr(project, field, value)
    project.slug = _slugify(payload.name)
    db.commit()
    db.refresh(project)
    record(db, user_id=user.id, action="project.updated", entity_type="project", entity_id=project.id)
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    db.delete(project)
    db.commit()
    record(db, user_id=user.id, action="project.deleted", entity_type="project", entity_id=project_id)


@router.post("/projects/sync-github", response_model=list[ProjectOut])
def sync_github(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Project]:
    """Import the user's authorized GitHub repositories as project evidence.

    Only public repos (or repos the user consents to) are imported. Fails
    gracefully if GitHub is unreachable or unauthenticated.
    """
    from app.config import get_settings
    from jf_github import GitHubClient, GitHubCredentials
    from ..models import CandidateProfile

    s = get_settings()
    profile = get_or_create_profile(db, user.id)
    creds = GitHubCredentials(token=s.github_token, username=(profile.github or "").rsplit("/", 1)[-1])
    client = GitHubClient(creds)
    try:
        repos = client.list_repositories()
    except Exception as exc:  # network/auth issues must not crash the API
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"GitHub synchronization failed. Retry. ({exc})")

    created: list[Project] = []
    for repo in repos[:50]:
        client.enrich(repo, with_readme=False)
        existing = db.query(Project).filter(Project.user_id == user.id, Project.github_url == repo.html_url).first()
        if existing:
            created.append(existing)
            continue
        langs = list(repo.languages.keys()) or ([repo.language] if repo.language else [])
        project = Project(
            user_id=user.id,
            name=repo.name,
            slug=_slugify(repo.name),
            description=repo.description or "",
            technologies=langs,
            skills_demonstrated=langs,
            github_url=repo.html_url or repo.url,
            source="github",
            is_fork=repo.is_fork,
            private=repo.private,
            evidence_strength="strong" if repo.stars >= 5 else "medium",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        created.append(project)
    record(db, user_id=user.id, action="github.synced", entity_type="project", detail=f"{len(created)} repos")
    return created


# ---------------------------------------------------------------------------
# CV upload
# ---------------------------------------------------------------------------


@router.post("/cv/upload")
def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    content = file.file.read()
    result = parse_cv(file.filename or "cv.pdf", content)
    if not result.ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.error)
    source_hash = hashlib.sha256(content).hexdigest()
    doc = CvDocument(user_id=user.id, name=file.filename or "Master CV", format=result.format, content_text=result.text, source_hash=source_hash)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    record(db, user_id=user.id, action="cv.uploaded", entity_type="cv_document", entity_id=doc.id)
    return {"id": doc.id, "name": doc.name, "format": doc.format, "chars": len(result.text)}