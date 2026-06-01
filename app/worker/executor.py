import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.models.agent_job import AgentJob
from app.services.etl_client import EtlClient
from app.workflows.base import WorkflowContext
from app.workflows.registry import get_workflow_class

logger = logging.getLogger("agent-worker")

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="agent-job")


def _append_step(job: AgentJob, step: str, status: str, detail: Optional[str]) -> None:
    logs: List[Dict[str, Any]] = list(job.steps_log or [])
    logs.append(
        {
            "step": step,
            "status": status,
            "detail": detail,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    job.steps_log = logs


def _run_job_sync(job_id: int, etl_token: Optional[str]) -> None:
    factory = get_session_factory()
    db: Session = factory()
    etl = EtlClient(token=etl_token)
    try:
        job = db.query(AgentJob).filter(AgentJob.id == job_id).first()
        if not job:
            return
        if job.status not in ("pending",):
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        job.steps_log = []
        db.commit()

        def log_step(step: str, status: str, detail: Optional[str] = None) -> None:
            _append_step(job, step, status, detail)
            db.commit()

        runtime = None
        try:
            runtime = etl.get_workspace_agent_runtime(job.workspace_id)
        except Exception as exc:
            log_step("load_workspace_settings", "warning", str(exc))

        wf_cls = get_workflow_class(job.workflow_key)
        workflow = wf_cls()
        ctx = WorkflowContext(
            db=db,
            job=job,
            etl=etl,
            log_step=log_step,
            extra={"workspace_runtime": runtime or {}},
        )

        result = workflow.run(ctx)
        job.output_payload = result.output
        job.report_payload = result.report
        job.etl_run_id = result.etl_run_id
        job.status = "succeeded"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("Job %s succeeded", job_id)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        job = db.query(AgentJob).filter(AgentJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_summary = str(exc)
            job.finished_at = datetime.now(timezone.utc)
            _append_step(job, "workflow", "failed", str(exc))
            db.commit()
    finally:
        etl.close()
        db.close()


def enqueue_job(job_id: int, etl_token: Optional[str] = None) -> None:
    _executor.submit(_run_job_sync, job_id, etl_token)
