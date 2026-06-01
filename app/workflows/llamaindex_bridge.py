"""
Optional LlamaIndex Workflows integration.

Import and extend when you define Event-driven graphs. The narrative workflow
can delegate to `run_llamaindex_workflow()` once events are wired.

Example (future):

    from llama_index.core.workflow import Workflow, StartEvent, StopEvent

    class NarrativeFlow(Workflow):
        ...
"""
from typing import Any, Dict


def llamaindex_available() -> bool:
    try:
        import llama_index.core  # noqa: F401
        return True
    except ImportError:
        return False


def workflow_status() -> Dict[str, Any]:
    return {
        "llamaindex_installed": llamaindex_available(),
        "note": "Use app.workflows.narrative_research for the current step-based runner.",
    }
