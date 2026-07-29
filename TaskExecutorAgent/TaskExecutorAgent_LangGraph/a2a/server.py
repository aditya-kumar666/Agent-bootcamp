"""Minimal A2A-style HTTP server for external agent communication.

The server exposes the existing LangGraph workflow externally while leaving the
internal GraphState orchestration unchanged.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from pydantic import ValidationError

from .registry import get_agent_card
from .schemas import A2ATaskRequest, A2ATaskResponse


WorkflowRunner = Callable[[str], dict[str, Any]]


def _state_to_external_result(state: dict[str, Any]) -> dict[str, Any]:
    """Project internal GraphState into a safe external response payload."""

    return {
        "plan": state.get("plan", ""),
        "code": state.get("code", ""),
        "review": state.get("review", ""),
        "reflection": state.get("reflection", ""),
        "evaluation": state.get("evaluation", ""),
    }


def create_handler(workflow_runner: WorkflowRunner):
    """Create an HTTP handler bound to the provided workflow runner."""

    class A2ARequestHandler(BaseHTTPRequestHandler):
        server_version = "TaskExecutorA2A/0.1"

        def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw)

        def do_GET(self) -> None:  # noqa: N802 - http.server naming convention
            if self.path == "/health":
                self._send_json(200, {"status": "ok", "agent": "task-executor-langgraph"})
                return
            if self.path == "/.well-known/agent.json":
                self._send_json(200, get_agent_card().model_dump())
                return
            self._send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802 - http.server naming convention
            if self.path != "/a2a/tasks":
                self._send_json(404, {"error": "Not found"})
                return

            try:
                request = A2ATaskRequest.model_validate(self._read_json_body())
                final_state = workflow_runner(request.task)
                response = A2ATaskResponse(
                    request_id=request.request_id,
                    status="completed",
                    result=_state_to_external_result(final_state),
                )
                self._send_json(200, response.model_dump())
            except ValidationError as ex:
                self._send_json(400, {"status": "failed", "error": ex.errors()})
            except Exception as ex:  # Keep external boundary resilient.
                self._send_json(500, {"status": "failed", "error": str(ex)})

        def log_message(self, format: str, *args: Any) -> None:
            print(f"[A2A] {self.address_string()} - {format % args}")

    return A2ARequestHandler


def run_a2a_server(workflow_runner: WorkflowRunner, host: str = "127.0.0.1", port: int = 8080) -> None:
    """Run the external A2A HTTP server."""

    server = ThreadingHTTPServer((host, port), create_handler(workflow_runner))
    print(f"[A2A] Listening on http://{host}:{port}")
    print(f"[A2A] Agent card: http://{host}:{port}/.well-known/agent.json")
    server.serve_forever()
