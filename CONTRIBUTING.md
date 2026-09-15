# Contributing

Thanks for wanting to improve JobForge, a **Sifuna Codex** product.

## Code of Conduct

Be respectful. This project has a philosophy: **quality over quantity**, human-in-the-
loop automation, and never crossing platform or legal boundaries. Contributions that
add *spam-like* automation, scraping of protected data, CAPTCHA/anti-bot bypass, or
credential fabrication will be rejected.

## Getting Started

1. Fork the repository.
2. Follow the install steps in [README.md](README.md).
3. Run the full test suite before you begin:

```bash
cd apps/api && python -m pytest
cd apps/web && npm test        # when frontend tests are added
```

4. Create a feature branch: `git checkout -b feat/my-change`.

## Development Workflow

- Keep the app runnable after every major change.
- Backend: Python type hints everywhere, Pydantic schemas for all input.
- Frontend: TypeScript strict mode, Tailwind utility classes, no new CSS libraries.
- Never commit `.env` or any secret.
- Never log credentials, tokens, email contents, or CV contents.
- Prefer the existing modular packages (`packages/*`) over adding new coupling.

## Requirements for a Good PR

- Tests that cover the change (unit + the relevant integration path).
- No regressions in `pytest apps/api/tests`.
- Security implications documented in the PR description if any.
- No giant files; keep modules focused.

## Testing

```bash
cd apps/api && python -m pytest -q

# Security scans (see SECURITY.md)
bandit -r apps/api packages -x "*/tests/*"
pip-audit
gitleaks detect --source .
```

## Commit Message Style

We use conventional commits:

```
feat(api): add job scoring weights endpoint
fix(web): resolve kanban drag-drop state
test(ai): cover prompt-injection payloads
security(api): rotate session tokens on privilege change
```

## Contact

Maintainer: **Sifuna Codex** — `codex@sifunacodex.dev`