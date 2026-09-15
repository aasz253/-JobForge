"""jf_email — email intelligence for JobForge."""

from .classifier import (  # noqa: F401
    ClassifiedEmail,
    EmailEvent,
    classify_email,
    extract_company_hint,
)