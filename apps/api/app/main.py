"""JobForge API — Sifuna Codex.

FastAPI application with security-hardened defaults:
- CORS restricted to configured origins
- security headers set on every response
- optional trusted-host filtering
- per-IP rate limiting on auth/import endpoints (in-route)
- structured audit logging for sensitive actions
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.ratelimit import limiter

from .api.routes import applications, auth, dashboard, finance, health, jobs, profile, settings
from .database import init_db

API_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="JobForge API",
    version=API_VERSION,
    description="AI-powered job acquisition automation by Sifuna Codex.",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

s = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=s.cors_origin_list or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    import time

    start = time.perf_counter()
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-XSS-Protection", "0")
    if get_settings().environment == "prod":
        response.headers.setdefault("Strict-Transport-Security", "max-age=15552000; includeSubDomains")
    # CSP: default deny-inline; API returns JSON only.
    response.headers.setdefault("Content-Security-Policy", "default-src 'none'; base-uri 'none'; frame-ancestors 'none'")
    response.headers.setdefault("X-Request-Id", str(int(start)))
    response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.middleware("http")
async def global_rate_limit(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    s = get_settings()
    if not limiter.hit(f"global:{client}", s.rate_limit_global_per_minute, 60):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Slow down."})
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Never leak internal error details to clients."""
    return JSONResponse(status_code=500, content={"detail": "Internal error."})


for router in (health.router, auth.router, profile.router, jobs.router, applications.router, dashboard.router, finance.router, settings.router):
    app.include_router(router, prefix=s.api_prefix)


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "app": s.app_name,
        "tagline": s.app_tagline,
        "made_by": s.app_made_by,
        "version": API_VERSION,
        "docs": "/api/docs",
    }