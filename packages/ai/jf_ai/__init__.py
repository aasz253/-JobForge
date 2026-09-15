"""jf_ai — AI provider abstraction, analysis and safety for JobForge."""

from .analyzer import (  # noqa: F401
    CandidateContext,
    JobAnalysis,
    JobContext,
    OpenAICompatibleAnalyzer,
    RuleBasedAnalyzer,
    get_analyzer,
)
from .risk import JobRiskContext, RiskFlag, RiskReport, analyze_job_risk  # noqa: F401
from .safety import (  # noqa: F401
    UnsupportedClaim,
    detection_pass,
    sanitize_analysis_output,
    system_guardrail,
    validate_claims,
    wrap_untrusted,
)

__all__ = [
    "get_analyzer",
    "CandidateContext",
    "JobAnalysis",
    "JobContext",
    "OpenAICompatibleAnalyzer",
    "RuleBasedAnalyzer",
    "JobRiskContext",
    "RiskFlag",
    "RiskReport",
    "analyze_job_risk",
    "UnsupportedClaim",
    "detection_pass",
    "sanitize_analysis_output",
    "system_guardrail",
    "validate_claims",
    "wrap_untrusted",
]