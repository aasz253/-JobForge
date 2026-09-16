"""Email intelligence — classification of recruitment mail.

Read-only, OAuth-only by design (no passwords). The classifier is pure and
public: it maps a subject + body to an EmailCategory and a recommended action.
Sensor logic is deliberately simple and testsuite-friendly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from jobforge_shared.constants import EmailCategory

CATEGORY_KEYWORDS: dict[EmailCategory, list[re.Pattern]] = {
    EmailCategory.INTERVIEW_INVITATION: [
        re.compile(r"interview invitation", re.I),
        re.compile(r"invited? (you )?(to|for an?) (a )?interview", re.I),
        re.compile(r"we 'd (like to|love to) (meet|talk|speak)", re.I),
        re.compile(r"schedule (an? |the |a )?interview", re.I),
        re.compile(r"next step.*interview", re.I),
    ],
    EmailCategory.TECHNICAL_ASSESSMENT: [
        re.compile(r"technical (assessment|test|challenge|assignment)", re.I),
        re.compile(r"take[ -]home", re.I),
        re.compile(r"code challenge", re.I),
        re.compile(r"(coding|technical) interview", re.I),
    ],
    EmailCategory.APPLICATION_RECEIVED: [
        re.compile(r"application (received|submitted)", re.I),
        re.compile(r"we (received|have received) your (application|resume|cv)", re.I),
        re.compile(r"thank you for (your )?applic", re.I),
        re.compile(r"acknowledg(e|ment).*application", re.I),
    ],
    EmailCategory.RECRUITER_CONTACT: [
        re.compile(r"recruit(e|ing)(er)? (from|at)", re.I),
        re.compile(r"saw your (profile|cv|resume)", re.I),
        re.compile(r"impressed by your", re.I),
        re.compile(r"found your (profile|cv) on", re.I),
    ],
    EmailCategory.FOLLOW_UP: [
        re.compile(r"following? up", re.I),
        re.compile(r"checking? in", re.I),
        re.compile(r"status of your application", re.I),
    ],
    EmailCategory.REJECTION: [
        re.compile(r"(unfortunately|sorry).*(not|unable to) (move forward|proceed|offer|shortlist)", re.I),
        re.compile(r"other candidates", re.I),
        re.compile(r"position (has been|was) filled", re.I),
        re.compile(r"decided to (go|move) (in )?(a )?different direction", re.I),
        re.compile(r"reject", re.I),
    ],
    EmailCategory.OFFER: [
        re.compile(r"offer (of employment|letter|stage)?", re.I),
        re.compile(r"we would like to offer you", re.I),
        re.compile(r"congratulations.*offer", re.I),
        re.compile(r"proposal for (contract|role)", re.I),
    ],
    EmailCategory.ACTION_REQUIRED: [
        re.compile(r"action required", re.I),
        re.compile(r"please (complete|confirm|respond|verify|update)", re.I),
        re.compile(r"deadline", re.I),
        re.compile(r"expiring", re.I),
    ],
}

# Priorities: interview/assessment/offer first, then rejection, then received, etc.
_ORDER: list[EmailCategory] = [
    EmailCategory.OFFER,
    EmailCategory.INTERVIEW_INVITATION,
    EmailCategory.TECHNICAL_ASSESSMENT,
    EmailCategory.ACTION_REQUIRED,
    EmailCategory.RECRUITER_CONTACT,
    EmailCategory.REJECTION,
    EmailCategory.APPLICATION_RECEIVED,
    EmailCategory.FOLLOW_UP,
]

RECOMMENDATIONS: dict[EmailCategory, str] = {
    EmailCategory.INTERVIEW_INVITATION: "Prepare technical interview and update the application status to INTERVIEW.",
    EmailCategory.TECHNICAL_ASSESSMENT: "Start the assessment early; set aside focused time.",
    EmailCategory.APPLICATION_RECEIVED: "Track as APPLICATION_RECEIVED; schedule a Day-5 follow-up.",
    EmailCategory.RECRUITER_CONTACT: "Record the recruiter in CRM and reply within 24h.",
    EmailCategory.FOLLOW_UP: "Reply and check the application timeline.",
    EmailCategory.REJECTION: "Record feedback in the learning engine and move on.",
    EmailCategory.OFFER: "Review the offer contract and negotiate if needed.",
    EmailCategory.ACTION_REQUIRED: "Reply/complete within 24 hours.",
    EmailCategory.OTHER: "No automated action needed.",
}


@dataclass
class EmailEvent:
    id: str = ""
    thread_id: str = ""
    sender: str = ""
    subject: str = ""
    body: str = ""
    received_at: datetime | None = None
    category: EmailCategory = EmailCategory.OTHER
    company_hint: str = ""
    role_hint: str = ""

    @property
    def pretty_category(self) -> str:
        return self.category.value.replace("_", " ").title()


@dataclass
class ClassifiedEmail:
    event: EmailEvent
    recommendation: str


def classify_email(subject: str, body: str = "", sender: str = "") -> ClassifiedEmail:
    """Classify a recruitment email into a category + recommended action."""
    haystack = f"{subject}\n{body}".lower()
    category = EmailCategory.OTHER
    for cand in _ORDER:
        if any(p.search(haystack) for p in CATEGORY_KEYWORDS[cand]):
            category = cand
            break

    event = EmailEvent(sender=sender, subject=subject, body=body, category=category)
    return ClassifiedEmail(event=event, recommendation=RECOMMENDATIONS[category])


def extract_company_hint(subject: str, sender: str = "") -> tuple[str, str]:
    """Best-effort company + role hints from the email (never authoritative)."""
    company = ""
    role = ""
    m = re.search(r"(?:at|from)?\s+([A-Z][A-Za-z0-9&. -]{2,40}?)(?:\s*[,;]|\s+is|\s+wants|\s+team)", subject or "")
    if m:
        company = m.group(1).strip()
    m2 = re.search(r"((?:[A-Za-z0-9/ +-]{2,40}?)(?:Engineer|Developer|Analyst|Architect|Manager|Intern|Director|Lead))", subject or "")
    if m2:
        role = m2.group(1).strip()
    if sender and not company:
        domain = (sender.split("@")[-1] if "@" in sender else "").split(".")[0]
        company = domain.capitalize()
    return company, role