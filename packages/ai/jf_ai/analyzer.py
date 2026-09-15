"""Job analysis engine — provider-agnostic.

`RuleBasedAnalyzer` always works (free), producing a deterministic analysis
from the scoring engine. `OpenAICompatibleAnalyzer` produces richer analysis
via a configured OpenAI-compatible / Ollama endpoint, gated by safety checks.

The AI provider layer is deliberately decoupled so JobForge never depends on
a single vendor. If no provider is configured, `AnalyzerFactory.get()` returns
the rule-based analyzer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import httpx
from jobforge_shared.constants import (
    AiProvider,
    EmploymentType,
    ExperienceLevel,
    RemoteStatus,
    RiskLevel,
)
from jf_scoring.engine import CandidateSkill, ProjectEvidence, ScoringEngine, extract_keywords

from . import risk as job_risk
from .safety import (
    detection_pass,
    sanitize_analysis_output,
    system_guardrail,
    validate_claims,
    wrap_untrusted,
)


@dataclass
class JobContext:
    title: str = ""
    company: str = ""
    description: str = ""
    location: str = ""
    remote_status: RemoteStatus | str = RemoteStatus.UNKNOWN
    employment_type: EmploymentType | str = EmploymentType.UNKNOWN
    experience_level: ExperienceLevel | str = ExperienceLevel.UNKNOWN
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "KSh"
    url: str = ""


@dataclass
class CandidateContext:
    profile_summary: str = ""
    headline: str = ""
    years_experience: int = 0
    preferred_remote: bool = True
    skills: list[CandidateSkill] = field(default_factory=list)
    projects: list[ProjectEvidence] = field(default_factory=list)


@dataclass
class JobAnalysis:
    summary: str = ""
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_requirement: str = ExperienceLevel.UNKNOWN.value
    matched_skills: list[str] = field(default_factory=list)
    skill_gaps: list[str] = field(default_factory=list)
    matching_projects: list[str] = field(default_factory=list)
    application_strategy: str = ""
    risks: list[str] = field(default_factory=list)
    risk_level: str = RiskLevel.LOW.value
    risk_flags: list[str] = field(default_factory=list)
    source: str = "rule-based"
    unsupported_claims: list[str] = field(default_factory=list)


def _build_analysis_from_score(
    job: JobContext,
    candidate: CandidateContext,
    score,
) -> JobAnalysis:
    analysis = JobAnalysis(source="rule-based")
    found = extract_keywords(job.description)
    analysis.required_skills = [s for s in found if s in score.missing_skills] or sorted(found)[:8]
    analysis.preferred_skills = [s for s in found if s not in analysis.required_skills]
    analysis.matched_skills = score.matched_skills
    analysis.skill_gaps = score.missing_skills
    analysis.matching_projects = score.matched_projects
    analysis.experience_requirement = score.by_category.get("detected_level") or ExperienceLevel.UNKNOWN.value

    summary = f"Role matches {score.total:.0f}/100 ({score.label})."
    if score.matched_skills:
        summary += f" Strong overlap on {', '.join(score.matched_skills[:5])}."
    if score.missing_skills:
        summary += f" Gaps: {', '.join(score.missing_skills[:5])}."
    analysis.summary = summary

    strategy_bits = []
    if score.matched_projects:
        strategy_bits.append(f"Lead with projects: {', '.join(score.matched_projects[:3])}.")
    if score.matched_skills:
        strategy_bits.append("Lead with core skills in the summary and CV.")
    if score.missing_skills:
        strategy_bits.append("Acknowledge/translate transferable experience toward missing areas; avoid overclaiming.")
    analysis.application_strategy = " ".join(strategy_bits) or "Position existing evidence and let interview conversation surface strengths."

    risks = []
    if score.by_category.get("detected_level") == ExperienceLevel.SENIOR.value and candidate.years_experience < 3:
        risks.append("Seniority expectation may exceed current formal experience.")
    if candidate.preferred_remote and job.remote_status == RemoteStatus.ON_SITE:
        risks.append("Role is on-site; location match required.")
    if score.by_category.get("detected_remote") == RemoteStatus.ON_SITE.value and "internation" in job.location.lower():
        risks.append("May require work authorization in a foreign location.")
    if not score.matched_projects:
        risks.append("No strong project evidence matched — consider adding one.")
    analysis.risks = risks

    risk_report = job_risk.analyze_job_risk(
        job_risk.JobRiskContext(
            title=job.title,
            company=job.company,
            description=job.description,
            url=job.url,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
        )
    )
    analysis.risk_level = risk_report.level.value
    analysis.risk_flags = [f"{f.description} ({f.evidence})" for f in risk_report.flags]

    claims = validate_claims(analysis.summary + " " + analysis.application_strategy)
    analysis.unsupported_claims = [f"{c.source_text} :: {c.reason}" for c in claims]
    return analysis


class RuleBasedAnalyzer:
    """Deterministic, free, offline-capable analyzer."""

    source = "rule-based"

    def __init__(self, weights: dict | None = None):
        self.engine = ScoringEngine(weights)

    def analyze(self, job: JobContext, candidate: CandidateContext) -> JobAnalysis:
        score = self.engine.compute(
            job_text=job.description,
            remote_status=job.remote_status,
            requested_level=job.experience_level,
            candidate_skills=candidate.skills,
            projects=candidate.projects,
            candidate_years_experience=candidate.years_experience,
            candidate_prefers_remote=candidate.preferred_remote,
        )
        return _build_analysis_from_score(job, candidate, score)


class OpenAICompatibleAnalyzer:
    """Analyzer over any OpenAI-compatible /chat/completions endpoint.

    Wraps the job description as untrusted data (prompt-injection defense),
    requests structured JSON, sanitizes the output and never lets external
    content control the system boundary.
    """

    source = "llm"

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        model: str = "gpt-4o-mini",
        weights: dict | None = None,
        fallback: "OpenAICompatibleAnalyzer | None" = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.models: list[str] = [m.strip() for m in (model or "").split(",") if m.strip()] or ["gpt-4o-mini"]
        self.fallback = fallback
        self.engine = ScoringEngine(weights)
        self.timeout = 60.0

    def _call(self, *, system: str, user: str) -> dict | None:
        """Try every model in the ring; return the first that yields valid JSON."""
        for model in self.models:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_guardrail(system)},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }
            try:
                resp = httpx.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            except Exception:
                continue
        return None

    def analyze(self, job: JobContext, candidate: CandidateContext) -> JobAnalysis:
        # Always produce the deterministic baseline first — the LLM can refine but
        # never replace the evidence-driven picture.
        base = _build_analysis_from_score(job, candidate, self.engine.compute(
            job_text=job.description,
            remote_status=job.remote_status,
            requested_level=job.experience_level,
            candidate_skills=candidate.skills,
            projects=candidate.projects,
            candidate_years_experience=candidate.years_experience,
            candidate_prefers_remote=candidate.preferred_remote,
        ))

        candidate_block = (
            f"CANDIDATE PROFILE (only facts below may be used):\n"
            f"- headline: {candidate.headline or 'n/a'}\n"
            f"- summary: {candidate.profile_summary or 'n/a'}\n"
            f"- years experience: {candidate.years_experience}\n"
            f"- skills: {', '.join(s.name for s in candidate.skills) or 'none'}\n"
            f"- projects: {', '.join(p.name for p in candidate.projects) or 'none'}"
        )
        # Job description arrives delimited as UNTRUSTED DATA.
        user = (
            "You are analyzing a job posting for the candidate described above.\n"
            f"{candidate_block}\n\n"
            f"{wrap_untrusted(job.description or '')}\n\n"
            "Return ONLY strict JSON with keys: summary, required_skills, preferred_skills, "
            "experience_requirement, application_strategy, risks. "
            "Do not reference the candidate's private details (email, phone, city of residence)."
        )
        system = (
            "You are JobForge, a job-acquisition analyst for a job seeker. You reason from "
            "evidence only; you never invent experience, metrics, employers or certifications."
        )
        processed = self._call(system=system, user=user)
        inj = detection_pass(job.description)
        if inj:
            base.risk_flags.append(f"Prompt-injection pattern detected and neutralized ({', '.join(inj[:3])})")
            base.risk_level = RiskLevel.MEDIUM.value

        if processed:
            processed = sanitize_analysis_output(processed)
            merged = base
            if processed.get("summary"):
                merged.summary = processed["summary"]
            for key in ("required_skills", "preferred_skills"):
                if processed.get(key):
                    setattr(merged, key, processed[key])
            if processed.get("experience_requirement"):
                merged.experience_requirement = processed["experience_requirement"]
            if processed.get("application_strategy"):
                merged.application_strategy = processed["application_strategy"]
            if processed.get("risks"):
                merged.risks = [r for r in processed["risks"] if isinstance(r, str)]
            # Keep evidence-derived fields authoritative:
            merged.matched_skills = base.matched_skills
            merged.skill_gaps = base.skill_gaps
            merged.matching_projects = base.matching_projects
            merged.source = "llm"

            # Anti-hallucination final pass: strip claims without profile backing.
            all_text = " ".join(merged.risks + [merged.summary, merged.application_strategy])
            claims = validate_claims(all_text)
            merged.unsupported_claims = [f"{c.source_text} :: {c.reason}" for c in claims]
        # Fallback ring: if no OpenRouter free model answered, try the local
        # Ollama endpoint before surrendering to the rule engine.
        if processed is None and self.fallback is not None:
            processed = self.fallback._call(system=system, user=user)
            if processed:
                merged = base
                for key in ("summary", "required_skills", "preferred_skills", "experience_requirement"):
                    if processed.get(key):
                        setattr(merged, key, processed[key])
                merged.application_strategy = processed.get("application_strategy") or base.application_strategy
                merged.risks = [r for r in processed.get("risks", []) if isinstance(r, str)]
                merged.source = "llm:fallback"
                processed_saved = processed
        if processed is None and self.fallback is not None:
            # Local Ollama rescues when every OpenRouter ring model was unreachable.
            try:
                local = self.fallback._make_request(system=system_guardrail(system), user=user_block)
                if local:
                    merged = _merge_analysis(base, local, source="llm", job=job, candidate=candidate)
                    merged.source = "llm:local-fallback"
                    base = merged
            except Exception:
                pass
        return base if processed is None else merged


def get_analyzer(
    provider: AiProvider | str = AiProvider.NONE,
    *,
    base_url: str = "",
    api_key: str = "",
    model: str = "",
    weights: dict | None = None,
    fallback_local: OpenAICompatibleAnalyzer | None = None,
) -> RuleBasedAnalyzer | OpenAICompatibleAnalyzer:
    """Factory: choose an analyzer matching the configured AI provider.

    OPENROUTER configures the free-model ring; if every model in the ring is
    unreachable, an optional Ollama fallback rescues the analysis locally.
    """
    provider = AiProvider(provider)
    if provider in (AiProvider.LOCAL, AiProvider.OPENAI_COMPATIBLE) and base_url:
        return OpenAICompatibleAnalyzer(
            base_url=base_url or "http://localhost:11434/v1",
            api_key=api_key,
            model=model or "qwen2.5-coder:7b",
            weights=weights,
            fallback=fallback_local,
        )
    if provider is AiProvider.OPENROUTER and api_key:
        return OpenAICompatibleAnalyzer(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model or "qwen2.5-coder:7b,meta-llama/llama-3.3-70b-instruct:free",
            weights=weights,
            fallback=fallback_local,
        )
    return RuleBasedAnalyzer(weights)