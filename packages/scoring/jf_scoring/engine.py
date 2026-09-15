"""Configurable 0-100 job scoring engine.

Pure rule-based (no LLM). Defaults total 100 and are user-configurable via
the `weights` mapping. The engine never rejects jobs on its own — scoring is
advisory, and manual override is always available.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from jobforge_shared.constants import DEFAULT_SCORE_WEIGHTS, ExperienceLevel, RemoteStatus, score_band, score_label

from .taxonomy import (
    HYBRID_HINTS,
    JUNIOR_HINTS,
    MID_HINTS,
    ONSITE_HINTS,
    REMOTE_HINTS,
    SENIOR_HINTS,
    SKILL_TAXONOMY,
    WEIGHT_CATEGORIES,
)


@dataclass
class CandidateSkill:
    """A skill the candidate claims in their profile (source of truth)."""

    name: str
    category: str = "other"  # human-readable group label
    proficiency: str = ""    # e.g. "Beginner / Intermediate / Advanced"
    evidence: str = ""       # optional free text

    def canonical_matches(self) -> list[str]:
        """Return canonical taxonomy skills whose alias set contains this name."""
        name = self.name.strip().lower()
        hits: list[str] = []
        for canonical, aliases in SKILL_TAXONOMY.items():
            bank = [canonical.lower(), *[a.lower() for a in aliases]]
            for a in bank:
                if not a:
                    continue
                if a == name or (len(name) >= 4 and (name in a or a in name)):
                    hits.append(canonical)
                    break
        return hits


@dataclass
class ProjectEvidence:
    """A repository/project the candidate can show as proof (source of truth)."""

    name: str
    skills: list[str] = field(default_factory=list)  # free-text skills
    description: str = ""


@dataclass
class ScoreBreakdown:
    total: float
    band: str
    label: str
    by_category: dict = field(default_factory=dict)
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    matched_projects: list[str] = field(default_factory=list)


def _normalize(text: str | None) -> str:
    return (text or "").lower()


def extract_keywords(text: str | None) -> set[str]:
    """Return canonical taxonomy skills mentioned anywhere in `text`."""
    found: set[str] = set()
    norm = _normalize(text)
    if not norm:
        return found
    for canonical, aliases in SKILL_TAXONOMY.items():
        bank = [canonical.lower(), *[a.lower() for a in aliases]]
        for a in bank:
            if not a:
                continue
            if re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", norm):
                found.add(canonical)
                break
    return found


def detect_remote_status(job_text: str | None, explicit: str | None = None) -> RemoteStatus:
    explicit = (explicit or "").strip()
    if explicit:
        e = explicit.lower()
        if "remote" in e and "hybrid" not in e:
            return RemoteStatus.REMOTE
        if "hybrid" in e:
            return RemoteStatus.HYBRID
        if "site" in e or "office" in e:
            return RemoteStatus.ON_SITE
        return RemoteStatus.UNKNOWN
    t = _normalize(job_text)
    if any(h in t for h in REMOTE_HINTS):
        return RemoteStatus.REMOTE
    if any(h in t for h in HYBRID_HINTS):
        return RemoteStatus.HYBRID
    if any(h in t for h in ONSITE_HINTS):
        return RemoteStatus.ON_SITE
    return RemoteStatus.UNKNOWN


def detect_experience_level(job_text: str | None) -> ExperienceLevel:
    t = _normalize(job_text)
    if any(h in t for h in SENIOR_HINTS):
        return ExperienceLevel.SENIOR
    if any(h in t for h in MID_HINTS):
        return ExperienceLevel.MID
    if any(h in t for h in JUNIOR_HINTS):
        return ExperienceLevel.JUNIOR
    return ExperienceLevel.UNKNOWN


def candidate_skill_categories(skills: list[CandidateSkill]) -> list[dict]:
    """Classify a candidate's claimed skills into human-readable groups."""
    result: list[dict] = []
    for skill in skills:
        canon = skill.canonical_matches()
        cat = skill.category or "other"
        for c in canon:
            for group, members in WEIGHT_CATEGORIES.items():
                if c in members:
                    cat = group
        result.append(
            {
                "name": skill.name,
                "category": cat,
                "proficiency": skill.proficiency,
                "evidence": skill.evidence,
            }
        )
    return result


class ScoringEngine:
    def __init__(self, weights: dict[str, float] | None = None):
        merged = {**DEFAULT_SCORE_WEIGHTS, **(weights or {})}
        total = sum(float(v) for v in merged.values()) or 1.0
        self.weights = {k: (float(v) / total) * 100.0 for k, v in merged.items()}

    def compute(
        self,
        *,
        job_text: str,
        remote_status: RemoteStatus | str | None = None,
        requested_level: ExperienceLevel | str | None = None,
        candidate_skills: list[CandidateSkill],
        projects: list[ProjectEvidence] | None = None,
        candidate_years_experience: int = 0,
        candidate_prefers_remote: bool = True,
    ) -> ScoreBreakdown:
        projects = projects or []
        job_hits = extract_keywords(job_text)

        candidate_canonicals: set[str] = set()
        for skill in candidate_skills:
            candidate_canonicals.update(skill.canonical_matches())

        matched = sorted(job_hits & candidate_canonicals)
        missing = sorted(job_hits - candidate_canonicals)

        # 1..n) per-category coverage: candidate covers the skills the job asked for
        category_scores: dict[str, float] = {}
        for cat, members in WEIGHT_CATEGORIES.items():
            cat_hits = job_hits & set(members)
            if not cat_hits:
                category_scores[cat] = 0.0
                continue
            have = len(cat_hits & candidate_canonicals) / len(cat_hits)
            category_scores[cat] = round(have, 3)

        # remote / international suitability
        rs = detect_remote_status(
            job_text,
            remote_status.value if isinstance(remote_status, RemoteStatus) else remote_status,
        )
        if rs == RemoteStatus.UNKNOWN:
            remote_score = 0.5
        elif rs == RemoteStatus.REMOTE:
            remote_score = 1.0 if candidate_prefers_remote else 0.5
        elif rs == RemoteStatus.HYBRID:
            remote_score = 0.8 if candidate_prefers_remote else 0.6
        else:
            remote_score = 0.3 if candidate_prefers_remote else 0.8

        # experience fit
        lvl = ExperienceLevel(requested_level or detect_experience_level(job_text))
        if lvl == ExperienceLevel.SENIOR:
            exp_score = min(candidate_years_experience / 6.0, 1.0)
        elif lvl == ExperienceLevel.MID:
            exp_score = min(candidate_years_experience / 4.0, 1.0)
        elif lvl == ExperienceLevel.JUNIOR:
            exp_score = min(candidate_years_experience / 2.0, 1.0) if candidate_years_experience > 0 else 0.5
        else:
            exp_score = 0.5

        # project evidence
        matched_projects: list[str] = []
        for p in projects:
            p_hits = extract_keywords(" ".join(p.skills)) if p.skills else set()
            if p_hits & job_hits:
                matched_projects.append(p.name)
        evidence_score = min(len(matched_projects) / 2.0, 1.0)

        # combine with weights
        category_map = {
            "ai_llm": category_scores.get("ai_llm"),
            "devsecops": category_scores.get("devsecops"),
            "security": category_scores.get("security"),
            "cloud": category_scores.get("cloud"),
            "python_development": category_scores.get("python_development"),
            "containers": category_scores.get("containers"),
        }
        contribution: dict[str, float] = {}
        for cat_key, w in self.weights.items():
            scalar = category_map.get(cat_key) if cat_key in category_map else {
                "remote_international": remote_score,
                "experience_fit": exp_score,
                "project_evidence": evidence_score,
            }[cat_key]
            contribution[cat_key] = round(w * (scalar or 0.0), 1)

        total = round(max(0.0, min(sum(contribution.values()), 100.0)), 1)

        by_category = {
            **contribution,
            "coverage": {k: round(v, 3) for k, v in category_scores.items()},
            "detected_remote": rs.value,
            "detected_level": lvl.value,
        }

        return ScoreBreakdown(
            total=total,
            band=score_band(total),
            label=score_label(total),
            by_category=by_category,
            matched_skills=matched,
            missing_skills=missing,
            matched_projects=matched_projects,
        )