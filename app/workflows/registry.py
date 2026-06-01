from typing import Dict, Type

from app.workflows.base import BaseWorkflow
from app.workflows.narrative_research import NarrativeResearchWorkflow

_REGISTRY: Dict[str, Type[BaseWorkflow]] = {
    NarrativeResearchWorkflow.key: NarrativeResearchWorkflow,
}


def get_workflow_class(key: str) -> Type[BaseWorkflow]:
    if key not in _REGISTRY:
        raise KeyError(f"Unknown workflow: {key}")
    return _REGISTRY[key]


def list_workflows() -> Dict[str, BaseWorkflow]:
    return {k: cls() for k, cls in _REGISTRY.items()}
