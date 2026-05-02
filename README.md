# Home Energy Advisor

Home Energy Advisor is a browser web app for creating home energy profiles and receiving AI-assisted advice around solar panels, home power stations, heat pumps, smart controls, and relevant EV charging.


## Planned Structure

```text
backend/   FastAPI, SQLite, LiteLLM, guardrails, tests
frontend/  Vue 3, TypeScript, fixed desktop UI, Playwright E2E
assents/   Provided house image asset
docs/      Product notes and take-home prompt
```

## Development Plan

Development should follow the predefined plans in order:

1. [Project Plan](docs/plans/project-plan.md)
2. [Backend Implementation Plan](docs/plans/backend-implementation-plan.md)
3. [Frontend Implementation Plan](docs/plans/frontend-implementation-plan.md)

## Environment

Default LLM behavior is configured for a local OpenAI-compatible server:

```text
LLM_PROVIDER=local
LLM_API_BASE=http://localhost:1234/v1
```

Use `LLM_PROVIDER=fake` for deterministic demo responses and tests.
