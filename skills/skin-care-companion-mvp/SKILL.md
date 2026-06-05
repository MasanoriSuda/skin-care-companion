---
name: skin-care-companion-mvp
description: Use when implementing or modifying the skin-care-companion Zennfes Spring 2026 / YouCam API MVP. Covers Codex-only spec-driven workflow, FastAPI backend, Flutter app, YouCam mock adapter, SQLite RAG recommendations, and xangi/Discord privacy constraints.
---

# Skin Care Companion MVP

## Workflow

1. Read `AGENTS.md` first, then inspect the relevant code and `docs/steering/` if the change is non-trivial.
2. Treat concrete user-provided acceptance criteria as the active specification. If privacy, persistence, or external API behavior is unclear, ask before expanding scope.
3. Keep the MVP runnable in mock mode. YouCam real API behavior belongs only in `apps/api/app/youcam/`.
4. Implement backend and mobile changes within their existing responsibility boundaries.
5. Update tests and README/docs when behavior or setup changes.

## Backend Guardrails

- Keep API keys and webhook URLs in backend environment variables only.
- `POST /api/skin/analyze` may temporarily persist an uploaded image, but must delete it after analysis and must not store it in SQLite.
- xangi/Discord-facing endpoints must return sanitized summaries only.
- Recommendations must be built from `products` seed data via retriever/service code. Do not invent products in prompts, constants, or LLM output.
- Preserve the retriever interface so SQLite FTS can later be replaced by vector search.

## Flutter Guardrails

- UI text is Japanese.
- Use `--dart-define=API_BASE_URL=...` for the backend URL.
- Do not embed YouCam, LLM, Discord, or xangi secrets in Flutter.
- Keep the diagnosis flow natural on mobile: image selection or camera, questionnaire, result, daily care, one-product recommendation, logs.

## Validation

- API: `cd apps/api && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest`
- Flutter: `cd apps/mobile && flutter test`
- Mock backend: `cd apps/api && uvicorn app.main:app --reload`
