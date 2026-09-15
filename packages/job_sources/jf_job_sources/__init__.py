"""jf_job_sources — modular job-source architecture and import tooling."""

from .base import JobSource, NormalizedJob  # noqa: F401
from .dedup import DedupDecision, canonical_external_key, check_duplicate, compute_content_hash  # noqa: F401
from .importer import (  # noqa: F401
    ExtractionResult,
    import_from_manual_paste,
    import_from_url,
)

__all__ = [
    "JobSource",
    "NormalizedJob",
    "DedupDecision",
    "canonical_external_key",
    "check_duplicate",
    "compute_content_hash",
    "ExtractionResult",
    "import_from_manual_paste",
    "import_from_url",
]