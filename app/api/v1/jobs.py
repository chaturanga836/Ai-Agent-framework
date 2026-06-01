from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.agent_job import AgentJob
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.worker.executor import enqueue_job
from app.workflows.registry import get_workflow_class

router = APIRouter()


def _to_response(job: AgentJob) -> JobResponse:
    return JobResponse.model_validate(job)


@router.post("/", response_model=JobResponse, status_code=202)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    try:
        get_workflow_class(payload.workflow_key)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job = AgentJob(
        workflow_key=payload.workflow_key,
        org_id=payload.org_id,
        workspace_id=payload.workspace_id,
        status="pending",
        input_payload=payload.input,
        correlation_id=payload.correlation_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    enqueue_job(job.id, etl_token=payload.etl_api_token)
    return _to_response(job)


@router.get("/", response_model=JobListResponse)
def list_jobs(
    workspace_id: int = Query(..., ge=1),
    status: Optional[str] = None,
    workflow_key: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(AgentJob).filter(AgentJob.workspace_id == workspace_id)
    if status:
        q = q.filter(AgentJob.status == status)
    if workflow_key:
        q = q.filter(AgentJob.workflow_key == workflow_key)
    total = q.count()
    rows = q.order_by(AgentJob.created_at.desc()).limit(limit).all()
    return JobListResponse(items=[_to_response(r) for r in rows], total=total)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(AgentJob).filter(AgentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_response(job)


@router.get("/{job_id}/report")
def get_job_report(job_id: int, db: Session = Depends(get_db)):
    """Report payload for etl-back Reports (data_root_path = report)."""
    job = db.query(AgentJob).filter(AgentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.report_payload:
        raise HTTPException(status_code=404, detail="No report payload on this job")
    return {"report": job.report_payload, "job_id": job.id, "workflow_key": job.workflow_key}
