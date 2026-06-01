"""HTTP client for etl-back — tools used by agent workflows."""
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings


class EtlClient:
    def __init__(self, token: Optional[str] = None):
        settings = get_settings()
        self.base_url = settings.etl_api_url.rstrip("/")
        self.timeout = settings.http_timeout_seconds
        bearer = token or settings.etl_api_token
        headers = {"Content-Type": "application/json"}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        self._headers = headers
        self._client = httpx.Client(base_url=self.base_url, headers=headers, timeout=self.timeout)

    def _platform_root(self) -> str:
        if self.base_url.endswith("/api/v1"):
            return self.base_url[: -len("/api/v1")]
        return self.base_url.rstrip("/")

    def close(self) -> None:
        self._client.close()

    def health(self) -> Dict[str, Any]:
        # etl-back exposes /health outside /api/v1
        r = httpx.get(
            f"{self._platform_root()}/health",
            headers=self._headers,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def get_pipeline_run(self, run_id: int) -> Dict[str, Any]:
        r = self._client.get(f"/sync/runs/{run_id}")
        r.raise_for_status()
        return r.json()

    def preview_report(self, run_id: int, definition_id: int) -> Dict[str, Any]:
        r = self._client.post(
            "/reports/preview",
            json={"run_id": run_id, "definition_id": definition_id},
        )
        r.raise_for_status()
        return r.json()

    def list_report_definitions(self, workspace_id: int, org_id: int = 1) -> Dict[str, Any]:
        r = self._client.get(
            "/reports/",
            params={"workspace_id": workspace_id, "org_id": org_id, "limit": 100},
        )
        r.raise_for_status()
        return r.json()

    def get_workspace_agent_runtime(self, workspace_id: int) -> Dict[str, Any]:
        """LLM + customer DB credentials configured in workspace settings UI."""
        r = self._client.get(f"/workspaces/{workspace_id}/agent-settings/runtime")
        r.raise_for_status()
        return r.json()
