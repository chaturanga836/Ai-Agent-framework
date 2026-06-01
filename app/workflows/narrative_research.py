"""
Narrative research workflow.

Produces a `report` payload compatible with etl-back Report definitions
(data_root_path = "report").

LLM credentials come from workspace settings (etl-back UI), not deployment .env.
"""
import json
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.workflows.base import BaseWorkflow, WorkflowContext, WorkflowResult


def _llm_from_context(ctx: WorkflowContext) -> Dict[str, Any]:
    runtime = ctx.extra.get("workspace_runtime") or {}
    return runtime.get("llm") or {}


def _extract_with_llm(
    topic: str,
    sources: List[Dict[str, Any]],
    llm: Dict[str, Any],
) -> Dict[str, Any]:
    settings = get_settings()
    api_key = llm.get("api_key") or settings.openai_api_key
    model = llm.get("model") or settings.openai_model or "gpt-4o-mini"
    provider = (llm.get("provider") or "openai").lower()
    base_url = llm.get("base_url")

    if not api_key:
        return _stub_report(
            topic,
            sources,
            "Configure API key under Workspace Settings → AI & Agent.",
        )

    if provider not in ("openai", "custom", "ollama"):
        return _stub_report(
            topic,
            sources,
            f"Provider '{provider}' not implemented yet; use openai or custom.",
        )

    try:
        from openai import OpenAI
    except ImportError:
        return _stub_report(topic, sources, "openai package not installed.")

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)

    prompt = (
        "Given the topic and source snippets, return JSON only with keys: "
        "topic, generated_at (ISO8601), narratives (list of "
        "{text, stance, verdict, confidence, sectors[], citations[]}), "
        "articles ({title, url, source}), rollup ({by_verdict: {}, by_sector: {}}). "
        "verdict must be one of: supported, disputed, unverifiable, misleading.\n\n"
        f"Topic: {topic}\n\nSources:\n{json.dumps(sources, default=str)[:12000]}"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)


def _stub_report(topic: str, sources: List[Dict[str, Any]], note: str) -> Dict[str, Any]:
    from datetime import datetime, timezone

    narratives = [
        {
            "text": f"Placeholder narrative about: {topic}",
            "stance": "neutral",
            "verdict": "unverifiable",
            "confidence": "low",
            "sectors": ["general"],
            "citations": [],
        }
    ]
    if sources:
        narratives[0]["citations"] = [s.get("url") for s in sources if s.get("url")][:3]

    return {
        "topic": topic,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "narratives": narratives,
        "articles": sources,
        "rollup": {
            "by_verdict": {"unverifiable": len(narratives)},
            "by_sector": {"general": len(narratives)},
        },
        "note": note,
    }


class NarrativeResearchWorkflow(BaseWorkflow):
    key = "narrative_research"
    name = "Narrative research"
    description = (
        "Research a topic, build narrative claims with verdicts and sector tags. "
        "Output matches ELT Reports `report` schema."
    )
    input_schema = {
        "type": "object",
        "required": ["topic"],
        "properties": {
            "topic": {"type": "string", "description": "Subject to research"},
            "max_sources": {"type": "integer", "default": 10},
            "etl_run_id": {
                "type": "integer",
                "description": "Optional pipeline run to pull last node output from",
            },
        },
    }

    def run(self, ctx: WorkflowContext) -> WorkflowResult:
        data = ctx.job.input_payload or {}
        topic = (data.get("topic") or "").strip()
        if not topic:
            raise ValueError("input.topic is required")

        llm = _llm_from_context(ctx)
        runtime = ctx.extra.get("workspace_runtime") or {}
        db_cfg = runtime.get("database") or {}
        if db_cfg.get("enabled"):
            ctx.log_step(
                "customer_database",
                "configured",
                f"{db_cfg.get('db_type', 'postgres')}://{db_cfg.get('host')}:"
                f"{db_cfg.get('port')}/{db_cfg.get('database')}",
            )

        max_sources = int(data.get("max_sources") or 10)
        etl_run_id = data.get("etl_run_id")

        sources: List[Dict[str, Any]] = []

        if etl_run_id:
            ctx.log_step("fetch_etl_run", "running", f"run_id={etl_run_id}")
            detail = ctx.etl.get_pipeline_run(int(etl_run_id))
            logs = detail.get("node_logs") or []
            last_out = None
            for log in reversed(logs):
                if log.get("status") == 2 and log.get("output_data"):
                    last_out = log["output_data"]
                    break
            if isinstance(last_out, dict):
                sources = last_out.get("articles") or last_out.get("sources") or []
                if isinstance(sources, dict):
                    sources = list(sources.values())
            ctx.log_step("fetch_etl_run", "succeeded", f"sources={len(sources)}")
        else:
            ctx.log_step("collect_sources", "skipped", "no etl_run_id — using stub sources")
            sources = [
                {
                    "title": f"Source placeholder for {topic}",
                    "url": "https://example.com/article",
                    "source": "stub",
                }
            ][:max_sources]

        ctx.log_step("extract_narratives", "running", None)
        report = _extract_with_llm(topic, sources[:max_sources], llm)
        ctx.log_step("extract_narratives", "succeeded", None)

        output = {
            "workflow_key": self.key,
            "topic": topic,
            "source_count": len(sources),
            "llm_model": llm.get("model"),
        }

        return WorkflowResult(
            output=output,
            report=report,
            etl_run_id=int(etl_run_id) if etl_run_id else None,
        )
