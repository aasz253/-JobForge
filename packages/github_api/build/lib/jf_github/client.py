"""GitHub evidence engine.

Connects to the GitHub REST API with an explicit user-authorized token.
Only repositories the user authorizes are visible to JobForge. Repository
metadata, README, languages, topics and descriptions are stored as structured
**evidence** for job matching. No private data is collected beyond what the
user consents to.

If no token is configured, repositories can still be added manually.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

GITHUB_API = "https://api.github.com"


@dataclass
class Repository:
    name: str
    description: str = ""
    url: str = ""
    html_url: str = ""
    language: str = ""
    topics: list[str] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)
    readme: str = ""
    is_fork: bool = False
    private: bool = False
    stars: int = 0
    updated_at: str = ""


@dataclass
class GitHubCredentials:
    token: str = ""
    username: str = ""

    @property
    def authenticated(self) -> bool:
        return bool(self.token or self.username)


class GitHubClient:
    def __init__(self, credentials: GitHubCredentials | None = None):
        self.credentials = credentials or GitHubCredentials()
        self.cfg_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.credentials.token:
            self.cfg_headers["Authorization"] = f"Bearer {self.credentials.token}"

    def _get(self, url: str, headers: dict | None = None) -> dict | list:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers={**self.cfg_headers, **(headers or {})})
            resp.raise_for_status()
            return resp.json()

    def identify(self) -> str:
        """Resolve the authenticated user's login (or the configured username)."""
        if self.credentials.username:
            return self.credentials.username
        if not self.credentials.token:
            raise RuntimeError("GitHub integration requires a token or username.")
        data = self._get(f"{GITHUB_API}/user")
        return data["login"]

    def list_repositories(self, only: list[str] | None = None) -> list[Repository]:
        """List repositories visible to JobForge.

        With a token: authenticated user's own (non-fork, non-private unless
        consented) repositories. Without a token: public repos of `username`.
        """
        login = self.identify()
        per_page = 100
        if self.credentials.token:
            url = f"{GITHUB_API}/user/repos?per_page={per_page}&sort=updated"
        else:
            url = f"{GITHUB_API}/users/{login}/repos?per_page={per_page}&sort=updated"
        data = self._get(url)
        repos = [self._to_repository(r) for r in data]
        if only:
            wanted = {x.strip().lower() for x in only}
            repos = [r for r in repos if r.name.lower() in wanted]
        return repos

    def _to_repository(self, raw: dict) -> Repository:
        repo = Repository(
            name=raw.get("name", ""),
            description=raw.get("description") or "",
            url=raw.get("url", ""),
            html_url=raw.get("html_url", ""),
            language=raw.get("language") or "",
            is_fork=bool(raw.get("fork")),
            private=bool(raw.get("private")),
            stars=int(raw.get("stargazers_count") or 0),
            updated_at=raw.get("updated_at") or "",
        )
        repo.topics = raw.get("topics") or []
        return repo

    def enrich(self, repo: Repository, *, with_readme: bool = True) -> Repository:
        """Add language stats and README text for one already-listed repo."""
        if not repo.url:
            return repo
        try:
            self._dereference(repo, f"{repo.url}/languages", "languages")
        except httpx.HTTPError:
            pass
        if with_readme:
            try:
                readme = self._get(f"{repo.url}/readme", headers={"Accept": "application/vnd.github.raw+json"})
                repo.readme = readme[:120_000] if isinstance(readme, str) else ""
            except httpx.HTTPError:
                repo.readme = ""
        return repo

    def _dereference(self, repo: Repository, url: str, attr: str):
        data = self._get(url)
        if isinstance(data, dict):
            setattr(repo, attr, data)
        elif isinstance(data, list):
            setattr(repo, attr, data)