"""CV parsing — extract text from PDF/DOCX uploads.

Parsing is read-only: the extracted text becomes the *master CV* content from
which versions are derived. Factual information is preserved and never altered.
Files are validated on type, size and the extracted text is what gets stored
(content is re-serialized rather than re-rendered).
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from pypdf import PdfReader  # type: ignore

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TEXT_CHARS = 500_000

SUPPORTED = {"pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@dataclass
class CvParseResult:
    ok: bool
    text: str = ""
    format: str = ""
    error: str = ""


def validate_upload(filename: str, content: bytes) -> CvParseResult:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext not in SUPPORTED:
        return CvParseResult(ok=False, error=f"Unsupported file type '.{ext}'. Use PDF or DOCX.")
    if len(content) > MAX_FILE_BYTES:
        return CvParseResult(ok=False, error="File is too large (max 8 MB).")
    return CvParseResult(ok=True, format=ext)


def parse_cv(filename: str, content: bytes) -> CvParseResult:
    validated = validate_upload(filename, content)
    if not validated.ok:
        return validated

    ext = validated.format
    try:
        if ext == "pdf":
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        else:  # docx
            from docx import Document  # type: ignore

            doc = Document(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)
            for table in doc.tables:
                for row in table.rows:
                    text += "\n" + " | ".join(cell.text for cell in row.cells)
    except Exception as exc:  # malformed uploads must not crash the API
        return CvParseResult(ok=False, error=f"Could not parse document: {exc}")

    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = text[:MAX_TEXT_CHARS]
    if len(text.strip()) < 20:
        return CvParseResult(ok=False, error="No readable text found in document.")
    return CvParseResult(ok=True, text=text, format=ext)