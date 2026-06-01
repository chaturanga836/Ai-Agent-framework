from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    workflow_key: str = Field(..., examples=["narrative_research"])
    workspace_id: int = Field(..., ge=1)
    org_id: int = 1
    input: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    etl_api_token: Optional[str] = Field(
        None,
        description="Optional Bearer token to call etl-back on behalf of the user.",
    )


class JobStepLog(BaseModel):
    step: str
    status: str
    detail: Optional[str] = None
    at: datetime


class JobResponse(BaseModel):
    id: int
    workflow_key: str
    org_id: int
    workspace_id: int
    status: str
    input_payload: Optional[Dict[str, Any]] = None
    output_payload: Optional[Dict[str, Any]] = None
    report_payload: Optional[Dict[str, Any]] = None
    error_summary: Optional[str] = None
    steps_log: Optional[List[Dict[str, Any]]] = None
    etl_run_id: Optional[int] = None
    correlation_id: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int


class WorkflowInfo(BaseModel):
    key: str
    name: str
    description: str
    input_schema: Dict[str, Any]
