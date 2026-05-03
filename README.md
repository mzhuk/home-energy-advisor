# Home Energy Advisor

Home Energy Advisor is a browser app that helps homeowners create multiple home profiles, generate practical energy-improvement advice, explore that advice through clickable areas on an energy-efficient house image, and continue one AI conversation per profile across solar panels, home power stations, heat pumps, smart controls, and relevant EV charging.

<img width="1679" height="1000" alt="image" src="https://github.com/user-attachments/assets/71db25c4-7948-4158-89aa-8542df9d50cb" />


## Plans

The implementation is intentionally plan-driven so another developer can trace decisions and scope changes quickly:

- [Project Plan](docs/plans/project-plan.md): shared product, API, data, LLM, guardrail, workflow, and repository contracts.
- [Backend Implementation Plan](docs/plans/backend-implementation-plan.md): FastAPI domain structure, SQLite repositories, LLM integration, guardrails, and backend tests.
- [Frontend Implementation Plan](docs/plans/frontend-implementation-plan.md): Vue layout, state, components, API client, chat behavior, and Playwright flow.

Use these files as the source of truth before changing behavior.

## Structure

```text
backend/   FastAPI, Pydantic, SQLite, LiteLLM, guardrails, pytest
frontend/  Vue 3, Vite, TypeScript, native fetch API client, Playwright
assents/   Provided house image asset
docs/      Plans, product notes, and take-home prompt
```

The backend exposes versioned routes under `/api/v1`, stores data in SQLite, and keeps all model calls behind the `app/llm/` layer. The frontend is a single desktop app shell with a profile sidebar, house scene, advice panel, focused chat, and global chat.

## AI Safety And Audit

The backend runs all AI communication through a dedicated guardrail pipeline before and after provider calls:

- PII masking: user messages are stored locally, then scrubbed before being sent to the LLM provider. The scrubber masks emails, phone numbers, address-like text, and explicit name fields; optional Presidio runtime support can add broader entity detection with `ENABLE_PRESIDIO_RUNTIME=true`.
- Prompt injection detection: suspicious requests such as ignoring prior instructions, revealing system or developer prompts, disabling safety rules, or exfiltrating conversation context are blocked before any provider call.
- Off-topic handling: clearly unrelated topics are blocked, while weaker relevance concerns are recorded as warnings so the assistant can stay focused on home energy advice without being brittle.
- Response validation: provider responses are scanned for prompt leakage and non-relevant content before they are returned to the UI. Invalid advice output falls back to deterministic advice instead of exposing malformed model output.
- Audit trail: safety events are written to `llm_audit_events`, including PII scrubs, prompt-injection blocks, off-topic warnings or blocks, post-validation failures, deterministic fallbacks, and provider errors. Audit records store a hash of the original text plus redacted structured details, not raw prompt content.

These checks are covered by backend guardrail and chat tests, and are intended to verify that sensitive user data does not flow to the AI provider, prompt-bypass attempts are detected, non-relevant AI interactions are handled, and AI communication remains inspectable during review.

## LLM Providers

Provider modes:

```text
fake       deterministic demo responses, no network calls
local      OpenAI-compatible local server, such as LM Studio
openai     remote OpenAI provider through LiteLLM
anthropic  remote Anthropic provider through LiteLLM
```

Local `.env` example:

```text
LLM_PROVIDER=local
LLM_MODEL=google/gemma-3-4b
LLM_API_BASE=http://localhost:1234/v1
LLM_API_KEY=lmstudio
LLM_MAX_RETRIES=0
```

### Local LLM setup
LM Studio: https://lmstudio.ai/
Make sure to enable API server in Developer Menu.

LLM Model https://lmstudio.ai/models/google/gemma-3-4b
App should work on arbitrary local model.


For deterministic demos and tests:

```text
LLM_PROVIDER=fake
```

For remote providers, set the matching key/model:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-mini

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-4-5-haiku-latest
```

## Local Run

Install backend dependencies:

```bash
cd backend
uv sync --locked
```

Run the backend:

```bash
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run the frontend:

```bash
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Useful checks:

```bash
cd backend
uv run pytest
uv run ruff check .
uv run ty check

cd frontend
npm run typecheck
npm run build
```

## Docker Compose

Run the full app:

```bash
docker compose up --build
```

Open:

```text
http://127.0.0.1:5173
```

Compose runs:

```text
backend   http://127.0.0.1:8000
frontend  http://127.0.0.1:5173
```

SQLite data is persisted in the `backend-data` Docker volume.

Compose supports provider switching with environment variables. If no provider is set in the shell or `.env`, it defaults to `fake`.

```bash
LLM_PROVIDER=fake docker compose up --build
LLM_PROVIDER=local docker compose up --build
LLM_PROVIDER=local DOCKER_LLM_MODEL=google/gemma-3-4b docker compose up --build
LLM_PROVIDER=openai OPENAI_API_KEY=... OPENAI_MODEL=gpt-5-mini docker compose up --build
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=... ANTHROPIC_MODEL=claude-4-5-haiku-latest docker compose up --build
```

For LM Studio from Docker, Compose defaults the backend to:

```text
LLM_API_BASE=http://host.docker.internal:1234/v1
```

This is intentionally different from a local backend run, where `LLM_API_BASE=http://localhost:1234/v1` is correct. To override the Docker-specific value, use:

```bash
DOCKER_LLM_API_BASE=http://host.docker.internal:1234/v1 LLM_PROVIDER=local DOCKER_LLM_MODEL=google/gemma-3-4b docker compose up --build
```

If the backend returns `503 Service Unavailable` in local-provider mode, first confirm the container was recreated after changing provider variables and that `docker compose config` shows `LLM_API_BASE: http://host.docker.internal:1234/v1`. Also make sure `LLM_MODEL` in the resolved Compose config matches one of the model IDs listed by LM Studio at `http://localhost:1234/v1/models`.

Reset containerized demo data:

```bash
docker compose down -v
```

Built using Codex and GPT-5.5.