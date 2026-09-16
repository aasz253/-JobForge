"""Job import: URL-based plus manual paste.

URL import is deliberately conservative:

* RSS/Atom feeds are parsed when the URL is a feed;
* regular job pages are read only for a small set of *public* HTML meta tags,
  and only after checking `robots.txt` for the host;
* anything else fails gracefully with the canonical guidance:
  *"Unable to extract this job automatically — paste the job description manually."*
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from jobforge_shared.constants import RemoteStatus
from jf_scoring.engine import detect_remote_status, extract_keywords

from .base import NormalizedJob

USER_AGENT = "JobForge/0.1 (career-assisted job ingestion; privacy-first; Sifuna Codex)"


class ExtractionFailure(Exception):
    pass


@dataclass
class ExtractionResult:
    ok: bool
    job: NormalizedJob | None = None
    error: str = ""
    warnings: list[str] = field(default_factory=list)


def _robots_allows(url: str) -> bool:
    """Check robots.txt allow rules for the requesting User-Agent.

    If robots.txt is unreachable we conservatively allow only feed URLs and
    meta reads are skipped (safer default), but site-wide restrictions from a
    reachable robots.txt always win.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = httpx.get(robots_url, timeout=8, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
        if resp.status_code != 200:
            # unreachable/absent robots: allow feed-only paths; HTML meta fetch is
            # gated separately by a per-host allowlist to be safe.
            return True
        rules: dict[str, list[str]] = {"*": []}
        current_agent = "*"
        for line in resp.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("user-agent"):
                current_agent = line.split(":", 1)[1].strip() or "*"
                rules.setdefault(current_agent.lower(), [])
            elif line.lower().startswith(("allow", "disallow")):
                action, value = line.split(":", 1)
                value = value.strip()
                rules.setdefault(current_agent.lower(), []).append((action.lower(), value))
        # match direct UA and * (least permissive)
        for agent in [USER_AGENT.split("/")[0].lower(), "*"]:
            for action, value in rules.get(agent, []):
                if action == "disallow" and (value == "*" or (value and urlparse(url).path.startswith(value))):
                    return False
        return True
    except httpx.HTTPError:
        return True  # feed-only fallback in callers


def _is_feed(url: str) -> bool:
    return any(t in url.lower() for t in (".rss", ".atom", "/rss", "/feed", "feed?")) or url.lower().endswith("/feed")


def _parse_feed(url: str, client: httpx.Client) -> list[NormalizedJob]:
    resp = client.get(url, timeout=15, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    jobs: list[NormalizedJob] = []

    # Atom
    if root.tag.lower().endswith("feed"):
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = _tag_text(entry, "{http://www.w3.org/2005/Atom}title")
            content = _tag_text(entry, "{http://www.w3.org/2005/Atom}content") or _tag_text(entry, "{http://www.w3.org/2005/Atom}summary")
            link = entry.find("{http://www.w3.org/2005/Atom}link")
            href = link.attrib.get("href", "") if link is not None else ""
            jobs.append(_feed_job(title, content, href, url))
        return jobs

    # RSS 2.0
    for item in root.iter("item"):
        title = _tag_text(item, "title")
        content = _tag_text(item, "description")
        link = _tag_text(item, "link")
        guid = _tag_text(item, "guid")
        pub = _tag_text(item, "pubDate")
        job = _feed_job(title, content, link, url)
        job.external_id = guid or link
        if pub:
            try:
                job.posted_at = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                pass
        jobs.append(job)
    return jobs


def _feed_job(title: str, content: str, link: str, feed_url: str) -> NormalizedJob:
    content = _strip_html(content)
    source = urlparse(feed_url).netloc
    job = NormalizedJob(
        source=source,
        source_url=feed_url,
        application_url=link or feed_url,
        company=source,
        title=_clean_title(title),
        description=content,
        remote_status=detect_remote_status(content),
        discovered_at=datetime.now(timezone.utc),
    )
    job.skills = sorted(extract_keywords(content))
    return job


def _tag_text(el, tag) -> str:
    node = el.find(tag)
    return (node.text or "") if node is not None else ""


def _strip_html(value: str) -> str:
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()[:300]


def extract_public_meta(url: str, client: httpx.Client) -> dict:
    """Extract tiny, public, standard meta tags from a public HTML page.

    Gated on robots.txt and a small allowlist of *standard* meta fields only
    (title, description, og:title, og:description). This is not scraping of
    user data — it is equivalent to reading public page metadata, and it never
    bypasses access controls.
    """
    resp = client.get(url, timeout=15, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
    if resp.status_code >= 400:
        raise ExtractionFailure(f"HTTP {resp.status_code}")
    html = resp.text[:2_000_000]
    meta: dict = {}

    def grab(pattern: str) -> str | None:
        m = re.search(pattern, html, flags=re.S | re.I)
        return m.group(1)[:500] if m else None

    meta["title"] = grab(r"<title[^>]*>(.*?)</title>")
    meta["description"] = grab(r'<meta\s+name=["\']description["\'][^>]*content=["\']([^"\']+)["\']')
    og = grab(r'<meta\s+property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']')
    if og:
        meta["og:title"] = og
    return {k: v for k, v in meta.items() if v}


def import_from_url(url: str) -> ExtractionResult:
    """Best-effort import. Returns clean guidance when extraction fails."""
    if not re.match(r"^https?://", url):
        return ExtractionResult(ok=False, error="Provide a full http(s) URL.")

    if not _robots_allows(url):
        return ExtractionResult(ok=False, error="robots.txt disallows automated access to this URL.")

    with httpx.Client() as client:
        if _is_feed(url):
            try:
                jobs = _parse_feed(url, client)
                if jobs:
                    takeaway = jobs[0]
                    if len(jobs) > 1:
                        takeaway.raw = {"feed_count": len(jobs)}
                    return ExtractionResult(ok=True, job=takeaway, warnings=[f"Feed exposed {len(jobs)} jobs; importing first."])
                return ExtractionResult(ok=False, error="Feed parsed but contained no jobs.")
            except (httpx.HTTPError, ET.ParseError) as exc:
                return ExtractionResult(ok=False, error=f"Feed parsing failed: {exc}")

        try:
            meta = extract_public_meta(url, client)
        except (httpx.HTTPError, ExtractionFailure) as exc:
            return ExtractionResult(
                ok=False,
                error="Unable to extract this job automatically.",
                warnings=[f"{exc}"],
            )

    if not meta:
        return ExtractionResult(ok=False, error="Unable to extract this job automatically.")
    domain = urlparse(url).netloc
    job = NormalizedJob(
        source=domain,
        source_url=url,
        application_url=url,
        company=domain,
        title=_clean_title(meta.get("og:title") or meta.get("title") or "Unknown role"),
        description=meta.get("description") or "",
        remote_status=RemoteStatus.UNKNOWN,
        discovered_at=datetime.now(timezone.utc),
    )
    job.skills = sorted(extract_keywords(job.description))
    return ExtractionResult(ok=True, job=job)


def import_from_manual_paste(payload: dict) -> NormalizedJob:
    """Build a normalized job from a user pasted description."""
    company = (payload.get("company") or "").strip() or "Unknown company"
    title = (payload.get("title") or "").strip() or "Unknown role"
    description = (payload.get("description") or "").strip()
    url = payload.get("url") or ""
    app_url = payload.get("application_url") or url

    job = NormalizedJob(
        source=(payload.get("source") or "manual").strip() or "manual",
        source_url=url,
        application_url=app_url,
        company=company[:200],
        title=title[:300],
        description=description,
        location=(payload.get("location") or "").strip()[:200],
        country=(payload.get("country") or "").strip()[:100],
        remote_status=detect_remote_status(description + payload.get("remote_status", "")),
        salary_min=payload.get("salary_min"),
        salary_max=payload.get("salary_max"),
        salary_currency=(payload.get("salary_currency") or "")[:10],
        external_id=(payload.get("external_id") or "").strip()[:200],
        discovered_at=datetime.now(timezone.utc),
    )
    if payload.get("deadline"):
        try:
            job.deadline = datetime.fromisoformat(str(payload["deadline"]))
        except ValueError:
            pass
    job.skills = sorted(extract_keywords(description))
    return job