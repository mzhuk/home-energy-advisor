# Backend Implementation Plan

## Backend Structure

Use layered modules:

```text
backend/app/
  main.py
  api/v1/routes/
  core/settings.py
  core/errors.py
  db/
  homes/
  advice/
  chat/
  llm/
  guardrails/
```

Implementation requirements:

- Routes are thin.
- Services contain business logic.
- Repositories contain SQLite access.
- Deterministic advice generation is a pure function.
- LLM calls happen only through `llm/`.
- Guardrails happen only through `guardrails/`.
- API schemas are Pydantic models.
- SQLite uses stdlib `sqlite3`; no ORM is needed for this demo.
- Use `asgi-correlation-id` for request IDs and log correlation.

## Data Model

SQLite tables:

```text
homes
  id
  name
  build_period
  home_size
  residents
  heating_system
  has_ev
  ai_context_json
  created_at
  updated_at

advice
  id
  home_id
  summary
  areas_json
  disclaimer
  provider
  used_fallback
  created_at

chat_messages
  id
  home_id
  role
  source
  content
  created_at

llm_audit_events
  id
  home_id
  event_type
  source
  severity
  original_text_hash
  details_json
  created_at
```

## Backend Implementation Sequence

### 1. Backend Setup

- Initialize `backend/pyproject.toml` with `uv`; set package/app name to `home-energy-advisor-backend`.
- Add runtime dependencies: `fastapi`, `uvicorn`, `pydantic-settings`, `litellm`, `asgi-correlation-id`, `presidio-analyzer`, `presidio-anonymizer`, `llm-guard`.
- Add dev dependencies: `pytest`, `httpx`, `pytest-mock`, `ruff`, `ty`.
- Add package layout under `backend/app/` with `__init__.py`, `main.py`, `api/v1/router.py`, and `api/v1/routes/health.py`.
- In `app/main.py`, expose an `app` object created by `create_app()` so tests can instantiate it.
- Mount all API routes under `/api/v1`; do not create unversioned API routes.
- Add CORS for `http://localhost:5173` and `http://127.0.0.1:5173` from settings.
- Implement `GET /api/v1/health` returning `status`, `provider`, `model`, `api_version`, and no secrets.
- Add documented commands:
  - `uv run uvicorn app.main:app --reload`
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run ty check`

Acceptance checks:

- `uv run uvicorn app.main:app --reload` starts from `backend/`.
- `GET /api/v1/health` returns `200`.
- `GET /api/health` and `GET /api/homes` are not registered.

### 2. Error And Request Infrastructure

- Implement `app/core/settings.py` using `pydantic-settings`; include DB path, CORS origins, LLM provider/model/base URL/API key, timeout, retry count, and temperature.
- Implement `app/core/errors.py` with:
  - `ErrorCode` literal/enum for all required error codes.
  - `AppError(code, message, status_code, details=None)`.
  - typed subclasses for not found, advice not found, LLM auth, LLM timeout, LLM unavailable, LLM bad response, prompt injection blocked, off-topic blocked, PII scrub failure, and internal errors.
- Add `asgi-correlation-id` middleware and use its correlation ID as `request_id` in error responses.
- Add exception handlers for `AppError`, `RequestValidationError`, and unexpected `Exception`.
- Format every error as `{ "error": { "code", "message", "details", "request_id" } }`.
- Ensure `RequestValidationError` maps to `validation_error` and keeps useful field-level details without exposing stack traces.
- Add lightweight structured logging that includes request ID, path, method, status, and app error code when present.

Acceptance checks:

- Invalid request bodies return the standard envelope with `validation_error`.
- Missing resources return the same envelope with `not_found`.
- No error response contains stack traces, raw prompts, API keys, or raw provider exceptions.

### 3. SQLite Repositories

- Implement `app/db/connection.py` using stdlib `sqlite3`; use row factory returning dict-like rows.
- Implement `app/db/schema.py` with idempotent `CREATE TABLE IF NOT EXISTS` statements for `homes`, `advice`, `chat_messages`, and `llm_audit_events`.
- Call schema initialization during app startup.
- Implement `app/db/json.py` helpers for deterministic JSON dump/load of list/dict columns.
- Implement `app/db/ids.py` with `new_id(prefix: str)` using URL-safe random or UUID-backed values.
- Implement repositories:
  - `homes/repository.py`: create, list ordered by `updated_at desc`, get by ID, touch `updated_at`.
  - `advice/repository.py`: save generated advice, get latest by `home_id`.
  - `chat/repository.py`: append message, list by `home_id` ordered by creation sequence/time.
  - `guardrails/audit_repository.py`: append audit event.
- Add foreign-key relationships where useful and enable `PRAGMA foreign_keys = ON`.
- Store datetimes as UTC ISO strings.

Acceptance checks:

- Repositories are the only modules issuing SQL.
- Tests can override the DB path with a temporary SQLite file.
- JSON columns round-trip without lossy string manipulation.

### 4. Homes Domain

- Implement `homes/models.py` or `homes/schemas.py` with enum classes for all profile fields and Pydantic request/response models.
- Add required profile name validation:
  - trim whitespace
  - non-empty after trimming
  - reasonable max length, e.g. 80 chars
- Implement `homes/ai_context.py` with a single mapping from each enum value to the exact saved AI instruction from the plan/product idea.
- Implement `homes/service.py`:
  - `create_home(request)`: trims name, generates AI context, persists record.
  - `list_homes()`: returns lightweight records ordered by latest update.
  - `get_home(home_id)`: returns profile, AI context, and latest advice if available.
- Implement routes in `api/v1/routes/homes.py`.
- Include OpenAPI examples for `POST /homes` and profile response.

Acceptance checks:

- Creating a home returns `home_...`, profile fields, AI context, timestamps.
- Listing homes supports multiple profiles and stable switching.
- Missing home returns `not_found`.

### 5. Deterministic Advice Engine

- Implement `advice/models.py` with `AreaId`, `Priority`, `AreaAdvice`, and `AdviceResponse` Pydantic models.
- Implement `advice/deterministic.py` as a pure function: `build_deterministic_advice(home, ai_context) -> AdviceDraft`.
- Always produce core areas: `solar`, `battery`, `heat_pump`, `smart_controls`.
- Include `ev_charging` only when `has_ev=true`; omit it completely otherwise.
- Encode the priority rules from the shared plan and keep all defaults deterministic.
- For each area, define title, priority, insight, first step, default prompt, and 2-3 suggested questions.
- Keep wording actionable and in scope; do not include unrelated insulation/window recommendations except as heat-pump readiness context.

Acceptance checks:

- The function has no DB, HTTP, or LLM dependencies.
- Same input always returns same area order and text.
- Rule tests cover old gas home, in-progress home, post-2000 heat pump home, large/5+ resident home, EV owner, and non-EV owner.

### 6. Advice Routes

- Implement `advice/service.py` with `get_latest_advice(home_id)` and `generate_advice(home_id)`.
- `GET /api/v1/homes/{home_id}/advice` returns latest persisted advice or `advice_not_found`.
- `POST /api/v1/homes/{home_id}/advice`:
  - loads home
  - builds deterministic draft
  - routes through fake provider when `LLM_PROVIDER=fake`
  - routes through real LLM flow when provider is local/openai/anthropic
  - persists final response
  - returns persisted advice with `id`, `provider`, `used_fallback`, and `created_at`
- If real LLM fails or invalid output cannot be repaired, persist deterministic fallback with `used_fallback=true`.
- Keep provider failure details out of public responses; write safe details to logs/audit.

Acceptance checks:

- Advice can be generated repeatedly and latest advice is updated.
- The API contract is the same for fake, real, and fallback advice.

### 7. LLM Client

- Implement `llm/client.py` with an interface/class exposing `generate_advice(messages, response_schema) -> str` and `chat(messages) -> str`.
- Implement `llm/litellm_client.py`; call LiteLLM only here.
- Map provider settings into LiteLLM args.
- Use timeout, retries, and temperature from settings.
- Use `api_base` and API key for local OpenAI-compatible mode.
- Implement `llm/fake_provider.py` with valid structured advice JSON and deterministic chat text by source.
- Include the demo limitation note in every fake chat response.
- Implement `llm/provider.py` or factory for `local`, `openai`, `anthropic`, and `fake`.
- Normalize LiteLLM exceptions into app errors.

Acceptance checks:

- Tests mock LiteLLM and never require network.
- Fake provider is deterministic and returns schema-valid output.
- Health reports configured provider/model without secrets.

### 8. Guardrails

- Implement `guardrails/pii.py` using Presidio analyzer/anonymizer when available.
- Mask emails, phone numbers, person names, and address-like entities.
- Return original text, scrubbed text, and a `changed` flag.
- Fail closed with `pii_scrubbed_and_failed` if scrubbing errors before an LLM call.
- Implement `guardrails/scanners.py`:
  - wrap LLM Guard input scanners: `TokenLimit`, `PromptInjection`, `Toxicity`, `BanTopics`
  - wrap output scanners: `Sensitive`, `Relevance`
  - provide deterministic regex fallback for prompt leakage and unsafe instructions so tests do not depend on model downloads
- Implement `guardrails/pipeline.py` with `run_input_hooks(home, source, message)` and `run_output_hooks(kind, text_or_json)`.
- Input hooks validate source, message length, EV source eligibility, prompt injection, topic relevance, toxicity/banned topics, and PII scrubbing.
- Output hooks detect prompt leakage, unsafe installation steps, off-topic responses, sensitive content, and exact unqualified ROI/savings claims.
- Implement `guardrails/audit.py` to persist audit events without storing raw PII in audit details.

Acceptance checks:

- Blocked input does not call LLM provider.
- PII-scrubbed input sends scrubbed text to LLM but stores original user message locally.
- Guardrail tests cover prompt injection, PII masking, off-topic input, unsafe output, prompt leakage output, and fallback audit events.

### 9. Prompt And Response Validation

- Implement `llm/prompts.py` with `PromptBuilder`.
- Advice messages include system guidance, allowed categories, home profile, AI context, deterministic draft priorities, JSON schema from `AdviceResponse`, and instruction to output JSON only.
- Chat messages include system guidance, home profile, AI context, latest advice, full profile-wide chat history, current source, and scrubbed message.
- Implement `llm/response_validator.py`:
  - extracts JSON from model text when needed
  - validates advice with Pydantic
  - validates area IDs and EV omission rules
  - validates chat response as non-empty, in-scope text
- Implement one repair attempt for malformed advice, then deterministic fallback.
- Add prompt tests verifying required safety text, full history inclusion, current source inclusion, and JSON-schema inclusion.

Acceptance checks:

- Route handlers never assemble prompts manually.
- Invalid model JSON cannot escape to the client.

### 10. Unified Chat

- Implement `chat/models.py` with role enum (`user`, `assistant`) and source enum.
- Implement `chat/service.py`:
  - `get_history(home_id)` returns ordered full profile-wide history.
  - `send_message(home_id, source, message)` runs input guardrails, stores original user message, builds prompt with scrubbed message and full history, calls provider, runs output guardrails, stores assistant response with same source.
- Validate `source=ev_charging` is rejected with `validation_error` or `off_topic_blocked` when the home has `has_ev=false`.
- Persist original user message before provider call only after pre-execution guardrails allow it.
- If provider fails after user message is stored, return controlled LLM error and do not store a fake assistant response unless deterministic fallback is explicitly used.
- Implement `GET /api/v1/homes/{home_id}/chat` and `POST /api/v1/homes/{home_id}/chat`.

Acceptance checks:

- Solar chat followed by global chat includes solar history in the global prompt.
- Global chat followed by hotspot chat includes global history in the hotspot prompt.
- Assistant response appears with the same source submitted by the user.

### 11. Backend Testing

- Add pytest fixtures for temporary DB, app instance, and test client.
- Test versioned routes and missing unversioned routes.
- Test error envelope and request ID.
- Test repositories and services separately where useful.
- Mock LiteLLM for provider tests.
- Keep all tests runnable without real LLM/network.

Required backend coverage:

- Home CRUD and ordering.
- Advice generation and missing advice.
- Fake provider responses and demo note.
- LiteLLM error mapping.
- Presidio PII scrubbing.
- LLM Guard prompt injection blocking.
- Post-response validation.
- Unified chat cross-source history.

