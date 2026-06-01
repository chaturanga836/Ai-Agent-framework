from fastapi import APIRouter, HTTPException

from app.schemas.job import WorkflowInfo
from app.workflows.registry import get_workflow_class, list_workflows

router = APIRouter()


@router.get("/", response_model=list[WorkflowInfo])
def list_workflow_catalog():
    items = []
    for wf in list_workflows().values():
        items.append(
            WorkflowInfo(
                key=wf.key,
                name=wf.name,
                description=wf.description,
                input_schema=wf.input_schema,
            )
        )
    return items


@router.get("/{workflow_key}", response_model=WorkflowInfo)
def get_workflow(workflow_key: str):
    try:
        wf = get_workflow_class(workflow_key)()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WorkflowInfo(
        key=wf.key,
        name=wf.name,
        description=wf.description,
        input_schema=wf.input_schema,
    )
