"""Job ingestion helpers: content hashing + duplicate detection.

Duplicate detection is based on content hash, external ID, and normalized
URL/company/title. When a duplicate is found, callers *merge metadata* onto
the existing record instead of creating a second job.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from .base import NormalizedJob


def _canon(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _canon_url(url: str | None) -> str:
    u = (url or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = u.rstrip("/")
    u = re.sub(r"([?#].*)$", "", u)
    return u


def compute_content_hash(job: NormalizedJob) -> str:
    """Content hash over stable identifying fields (company + title + description)."""
    payload = "|".join(
        [
            _canon(job.company),
            _canon(job.title),
            (job.description or "").strip().lower(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_external_key(job: NormalizedJob) -> str:
    if job.external_id:
        return f"ext:{_canon(job.source)}:{_canon(job.external_id)}"
    return f"url:{_canon_url(job.application_url or job.source_url)}"


@dataclass
class DedupDecision:
    duplicate: bool
    reason: str = ""
    existing_key: str = ""


def check_duplicate(job: NormalizedJob, existing: list[NormalizedJob]) -> DedupDecision:
    """Decide whether `job` duplicates any of `existing` records.

    Comparison order:
      1. same external ID (+ same source)
      2. same canonical URL
      3. same content hash (company + title + description)
    """
    incoming_hash = compute_content_hash(job)
    incoming_key = canonical_external_key(job)

    for old in existing:
        if incoming_key and incoming_key == canonical_external_key(old):
            return DedupDecision(True, "same external id/url", incoming_key)
        if old.hash and incoming_hash == old.hash:
            return DedupDecision(True, "same content hash", f"hash:{incoming_hash[:16]}")
    return DedupDecision(False, "", "")