from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.agent_job import AgentJob
from app.services.etl_client import EtlClient


@dataclass
class WorkflowContext:
    db: Session
    job: AgentJob
    etl: EtlClient
    log_step: Callable[[str, str, Optional[str]], None]
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    output: Dict[str, Any]
    report: Optional[Dict[str, Any]] = None
    etl_run_id: Optional[int] = None


class BaseWorkflow(ABC):
    key: str
    name: str
    description: str
    input_schema: Dict[str, Any]

    @abstractmethod
    def run(self, ctx: WorkflowContext) -> WorkflowResult:
        raise NotImplementedError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
