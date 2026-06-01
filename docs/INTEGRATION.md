# Integration with ELT platform

## Repos

| Repo | Role |
|------|------|
| `etl-back` | Auth, pipelines, runs, **Reports** API |
| `elt-frontend` | UI (Reports + future Agent jobs UI) |
| `Ai-Agent-framework` | This service — workflows & agent jobs |
| `etl-deployment` | Compose bundle (add `agent-api` service) |

## Recommended request flow

```
Browser → etl-back (Keycloak) → Ai-Agent-framework → etl-back (tools)
```

The frontend should **not** call the agent service directly in production. Add a proxy in `etl-back`:

- `POST /api/v1/agent-jobs` → forwards to `POST /api/v1/jobs` here
- Stores `correlation_id` / user context on both sides

## Report output contract

Workflows should set `report_payload` compatible with **Reports** presets:

```json
{
  "topic": "...",
  "generated_at": "ISO8601",
  "narratives": [],
  "articles": [],
  "rollup": { "by_verdict": {}, "by_sector": {} }
}
```

Fetch from this service:

`GET /api/v1/jobs/{id}/report` → `{ "report": { ... } }`

Use `data_root_path: "report"` in etl-back report definitions, or pass the object directly to `/reports/preview` after materializing a pipeline run.

## Environment (operator / deployment only)

| Variable | Description |
|----------|-------------|
| `ETL_API_URL` | **Required** — etl-back base URL |
| `DATABASE_URL` | Agent job store (`elt_agent` DB), not customer data |
| `ETL_API_TOKEN` | Optional default Bearer |

## Customer configuration (UI)

Workspace admins set in **elt-frontend → Workspace Settings → AI & Agent**:

- OpenAI / Anthropic / Ollama / custom provider
- Model (any id)
- API key
- Optional customer Postgres (for agent tools)

Jobs must pass `etl_api_token` (user JWT) so the agent can call:

`GET /api/v1/workspaces/{id}/agent-settings/runtime`

`elt_agent` is created by `etl-deployment/scripts/init-db.sql` on first Postgres startup. Tables are created on agent service startup (`create_all`).

## etl-deployment snippet

```yaml
  agent-api:
    build: ../Ai-Agent-framework
    ports:
      - "8100:8100"
    environment:
      ETL_API_URL: http://etl-backend:8000/api/v1
    depends_on:
      - etl-backend
```

## Next steps

1. `etl-back`: `agent_jobs` table + proxy routes
2. `elt-frontend`: Agent jobs page + link report export to job output
3. Replace step loop in `narrative_research.py` with LlamaIndex `Workflow` events
4. Add tools: search, scrape via etl-back connections API
