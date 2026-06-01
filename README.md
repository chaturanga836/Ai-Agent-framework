# ELT Agent Service (Ai-Agent-framework)

Microservice for **agent workflows** (LlamaIndex Workflows–ready) that complements the ELT platform (`etl-back`, `elt-frontend`).

- **Pipelines** = deterministic ETL graphs in `etl-back`
- **This service** = adaptive research / multi-step jobs with tool calls back into ELT APIs
- **Reports** = render output via `etl-back` `/reports` (use `report` JSON schema)

## Configuration model

| Who | What |
|-----|------|
| **Operator** (`.env`) | `ETL_API_URL`, `DATABASE_URL` for agent job metadata (`elt_agent`) |
| **Customer** (UI) | OpenAI key, model, customer database — Workspace Settings → **AI & Agent** |

## Database (deployment)

Uses the **same PostgreSQL server** as `etl-back`, with a separate database **`elt_agent`** (agent jobs only — not customer DB).

If you use `etl-deployment`, `scripts/init-db.sql` already creates `elt_agent`. For an existing Postgres volume, run once:

```sql
CREATE DATABASE elt_agent;
```

Copy `.env.example` → `.env` and set `DATABASE_URL` (or `POSTGRES_*` fields).

## Quick start

```bash
cd Ai-Agent-framework
cp .env.example .env
# Edit DATABASE_URL to match your Postgres user/password/host
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m app.main
```

API: [http://localhost:8100/docs](http://localhost:8100/docs)

### Docker

```bash
cp .env.example .env
docker compose up --build
```

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Service + LlamaIndex install hint |
| GET | `/api/v1/workflows/` | Workflow catalog |
| POST | `/api/v1/jobs/` | Start job (202, runs in background) |
| GET | `/api/v1/jobs/{id}` | Job status & output |
| GET | `/api/v1/jobs/{id}/report` | `report` object for ELT Reports |

### Example: narrative research

```bash
curl -X POST http://localhost:8100/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_key": "narrative_research",
    "workspace_id": 1,
    "input": { "topic": "AI will replace jobs" }
  }'
```

Poll `GET /api/v1/jobs/1` until `status` is `succeeded`, then `GET /api/v1/jobs/1/report`.

Optional: pass `etl_run_id` in `input` to pull articles from an existing pipeline run. Pass `etl_api_token` on the job body when calling ETL APIs as a user.

## Workflows

| Key | Description |
|-----|-------------|
| `narrative_research` | Topic → narratives + verdicts + sectors (`report` schema) |

Implement new workflows under `app/workflows/` and register in `app/workflows/registry.py`.

LlamaIndex graphs can live in `app/workflows/llamaindex_bridge.py` and replace the step runner over time. See `docs/INTEGRATION.md`.

## Project layout

```
app/
  main.py              # FastAPI entry
  api/v1/              # HTTP routes
  workflows/           # Workflow implementations
  worker/executor.py   # Background job runner
  services/etl_client.py
  models/agent_job.py
```

## Minimal install (no LlamaIndex)

```bash
pip install -r requirements-minimal.txt
```

Narrative workflow still runs with OpenAI optional; LlamaIndex features report as not installed on `/health`.
