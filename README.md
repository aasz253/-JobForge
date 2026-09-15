# JobForge

**AI-powered career acquisition automation by Sifuna Codex.**

> Find. Qualify. Apply. Advance.

JobForge is a free-first, privacy-conscious, AI-assisted job acquisition operating
system. It helps a job seeker discover relevant jobs, analyze and score them against
real skills, tailor legitimate application materials, track applications, monitor
recruitment email, manage follow-ups, and measure progress toward a financial
employment goal (default target: **KSh 1,000,000**, fully configurable).

**JobForge is NOT a spam bot.** It never fabricates credentials, never scrapes
protected data, never bypasses anti-bot systems, and **never submits an external
application without explicit human approval**.

---

## Features

- **Job Discovery & Ingestion** — modular job-source architecture (RSS/API/manual/URL
  import), content-hash duplicate detection, normalized job records.
- **AI Job Analysis & Scoring** — 0–100 score with configurable weights, rule-based
  fallback so it works with zero AI cost, prompt-injection defense for malicious job
  descriptions.
- **Job Risk Analysis** — flags potential recruitment-fraud indicators.
- **Candidate Profile & Skill Database** — structured, editable DevSecOps skill graph.
- **CV Engine** — master CV (PDF/DOCX) ingestion + tailored CV versions with
  AI-generated drafts that never invent facts.
- **Cover Letter & Application Answer Engine** — role-specific drafts, clearly marked
  "AI GENERATED DRAFT", human review required.
- **Application Workspace & Tracker** — kanban tracker, per-job workspace, quality
  check before submission, explicit approval requirement.
- **GitHub Evidence Engine** — import authorized repositories as structured proof of
  skills, and match projects against job requirements.
- **Financial Goal Tracker** — track income toward a configurable target.
- **Email Intelligence** — optional read-only OAuth email connector that classifies
  recruitment mail. Connections are never password-based and data is encrypted.
- **Follow-up Engine** — scheduled follow-up drafts (Day 5/10/20), never auto-sent.
- **Recruiter CRM, Interview Prep, Analytics, Daily/Weekly Reports** — planned
  modules (see Roadmap).
- **Human-in-the-Loop** — three application modes; external submission always requires
  user action unless a platform API explicitly authorizes automation and the user
  deliberately enables it.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

```
apps/web   — Next.js (App Router), React, TypeScript, Tailwind CSS
apps/api   — Python FastAPI, SQLAlchemy (PostgreSQL / SQLite)
packages/  — shared Python packages (AI abstraction, scoring, job sources, GitHub,
             email, CV)
```

## Tech Stack

- **Frontend:** Next.js, React, TypeScript (strict), Tailwind CSS
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** PostgreSQL (production), SQLite (local dev)
- **Auth:** salted PBKDF2 password hashing, signed session tokens, secure cookies
- **AI:** provider-agnostic abstraction — `local` (Ollama), `openai_compatible`,
  `none` (rule-based). Default `none` = zero API cost, fully functional core.

## Installation

Prerequisites: Python 3.11+, Node.js 20+, Docker or Podman (optional, for PostgreSQL).

```bash
# 1. Clone / enter the repo
cd jobforge

# 2. Backend
python -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
pip install -e packages/shared packages/ai packages/scoring packages/job_sources packages/github_api packages/email_intel packages/cv_utils

cp .env.example .env                  # configure variables
```

```bash
# 3. Frontend
cd apps/web
npm install
```

### Local development (recommended)

```bash
# Terminal A — API (SQLite by default)
cd apps/api && uvicorn app.main:app --reload --port 8000

# Terminal B — Web
cd apps/web && npm run dev
```

Open http://localhost:3000 — the web app proxies API calls to `http://localhost:8000`.

### Docker / Podman (one command)

```bash
docker compose up --build
```

Or with Podman (Docker-compatible):

```bash
export DOCKER_HOST=unix:///run/user/$(id -u)/podman/podman.sock
podman compose up --build
```

## Environment Variables

Copy `.env.example` to `.env`. All secrets live outside the source tree; `.env` is
git-ignored. Key variables:

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL. Default `sqlite:///./jobforge.db` |
| `SECRET_KEY` | Session signing key. **Generate a random one.** |
| `AI_PROVIDER` | `none` (default, rule-based) · `local` · `openai_compatible` |
| `AI_BASE_URL` | Base URL for OpenAI-compatible/local endpoints |
| `AI_API_KEY` | Optional API key for OpenAI-compatible endpoints |
| `AI_MODEL` | Model identifier used by the provider |
| `GITHUB_TOKEN` | Optional GitHub personal access token (authorized repos only) |
| `CORS_ORIGINS` | Comma-separated allowed origins for the web app |
| `APP_NAME` / `APP_TAGLINE` | Branding overrides |

## AI Configuration

JobForge works out of the box with **no AI configured** (rule-based keyword scoring and
analysis). To enable LLM analysis:

```ini
AI_PROVIDER=openai_compatible    # or "local"
AI_BASE_URL=http://localhost:11434/v1   # Ollama example
AI_MODEL=qwen2.5-coder:7b
```

External job descriptions are treated as **untrusted data** — see
[SECURITY.md](SECURITY.md) for prompt-injection defenses.

## GitHub Integration

Optional. Provide `GITHUB_TOKEN` and the app imports only the repositories the user
authorizes. Repository metadata, README, languages and topics are stored as structured
**evidence** and matched against job requirements. Without a token, repositories can be
added manually.

## Email Integration

Optional and read-only. Connect via OAuth (no passwords stored). Incoming recruitment
mail is classified into categories (interview invitation, rejection, offer, ...) and
drives suggested actions. Connections can be disconnected and synchronized data
deleted at any time.

## Job Sources

Modular `JobSource` interface — add new sources by implementing
`fetch_jobs()` / `normalize_job()` / `health_check()`. Sources are only used where
their terms of service permit access.

## Security

- Hashed passwords (PBKDF2-HMAC with per-user salt), rotating session tokens.
- Input validation on every endpoint, ORM parameterization (no SQL injection).
- CSRF protection for session cookies, secure headers, rate limiting.
- Strict content-Security-Policy style config on the web app.
- Audit logging of sensitive operations.
- Prompt-injection defense for untrusted job descriptions.
- No secrets in the repository; `.env` git-ignored; CI runs secret scans.

See [SECURITY.md](SECURITY.md) and [our responsible disclosure process](#).

## Privacy

Career data is encrypted at rest where appropriate, never sold, never shared. Users
can export, disconnect integrations, and delete all their data at any time.

## Screenshots

*To be added.*

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the phased plan (V1 → V5).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

---

*Built by **Sifuna Codex** to demonstrate how AI engineering, DevSecOps, cybersecurity
and automation transform the job acquisition process.*