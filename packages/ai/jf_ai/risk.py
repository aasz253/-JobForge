"""Job risk analyzer.

Scans an imported job description for indicators of recruitment fraud, scams,
or phishing. Returns a structured risk report without making accusations —
only listing potential risk indicators.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from jobforge_shared.constants import RiskLevel


@dataclass
class RiskFlag:
    description: str
    evidence: str  # matched fragment / reason


@dataclass
class RiskReport:
    level: RiskLevel
    flags: list[RiskFlag] = field(default_factory=list)
    score: float = 0.0  # internal 0..1 risk score


_PAYMENT_FLAGS = [
    ("payment_requested", "requests payment or fees from the candidate", [
        "pay for", "training fee", "registration fee", "processing fee",
        "deposit", "transfer bitcoin", "wire money", "money order",
    ]),
    ("crypto_requested", "requests cryptocurrency payment", [
        "bitcoin", "crypto", "ethereum", "usdt", "blockchain payment",
    ]),
]

_IDENTITY_FLAGS = [
    ("passwords_requested", "requests passwords or credentials", [
        "your password", "bank password", "social security password",
    ]),
    ("unnecessary_identity", "requests unnecessary identity documents before interview", [
        "send passport", "send national id", "send driver license",
        "copy of id before interview", "photo of your id",
    ]),
]

_COMMUNICATION_FLAGS = [
    ("unusual_only", "recruitment only via personal messaging apps", [
        "whatsapp only", "telegram only", "whatsapp me",
        "message me on whatsapp", "message me on telegram",
    ]),
    ("non_professional_email", "communicates from a non-corporate email", [
        "gmail.com", "yahoo.com", "hotmail.com", "proton.me",
    ]),
]

_SALARY_FLAGS = [
    ("unrealistic_salary", "salary figures that appear unrealistic for a standard role", []),
]

_SCAM_PHRASES = [
    "be your own boss",
    "pyramid",
    "mlm",
    "multi level marketing",
    "get rich quick",
    "no experience needed for six figures",
    "unlimited earning potential",
]


@dataclass
class JobRiskContext:
    """Minimal job metadata available to the risk analyzer."""

    title: str = ""
    company: str = ""
    description: str = ""
    url: str = ""
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "USD"
    application_url: str = ""


def analyze_job_risk(ctx: JobRiskContext) -> RiskReport:
    """Return a risk report for the given job data."""
    flags: list[RiskFlag] = []
    norm = (ctx.description + " " + ctx.url).lower()

    # payment / identity / comms
    for group in (_PAYMENT_FLAGS, _IDENTITY_FLAGS, _COMMUNICATION_FLAGS):
        for desc_key, desc, phrases in group:
            for phrase in phrases:
                if phrase.lower() in norm:
                    flags.append(RiskFlag(description=desc, evidence=f'"{phrase}"'))
                    break

    # scam phrases
    for phrase in _SCAM_PHRASES:
        if phrase in norm:
            flags.append(RiskFlag(description="contains common scam phrase", evidence=f'"{phrase}"'))
            break

    # salary anomaly: very high figures without clear context
    if ctx.salary_max and ctx.salary_max > 500_000:
        if ctx.salary_currency.upper() == "KSH" and ctx.salary_max > 10_000_000:
            flags.append(RiskFlag(description="unrealistically high salary reported", evidence=f"{ctx.salary_max} {ctx.salary_currency}"))
        elif ctx.salary_currency.upper() in ("USD", "EUR", "GBP") and ctx.salary_max > 500_000:
            flags.append(RiskFlag(description="unrealistically high salary reported", evidence=f"{ctx.salary_max} {ctx.salary_currency}"))

    # suspicious URL / domain signals
    suspicious_domain_patterns = [".top", ".xyz", ".buzz", "bit.ly", "tinyurl"]
    for pat in suspicious_domain_patterns:
        if pat in ctx.url.lower():
            flags.append(RiskFlag(description="suspicious TLD or URL shortener", evidence=ctx.url))
            break

    # download / remote-access red flags
    download_patterns = [
        "download software", "install remote desktop", "anydesk", "teamviewer",
        "remote access required", "rdo software",
    ]
    for phrase in download_patterns:
        if phrase in norm:
            flags.append(RiskFlag(description="requests software download or remote access", evidence=f'"{phrase}"'))
            break

    # compute risk level
    risk_score = min(len(flags) * 0.2, 1.0)
    if risk_score >= 0.6:
        level = RiskLevel.HIGH
    elif risk_score >= 0.3:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    return RiskReport(level=level, flags=flags, score=risk_score)