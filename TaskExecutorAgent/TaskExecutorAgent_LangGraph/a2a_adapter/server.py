"""A2A SDK-backed HTTP server for external agent communication.

The server exposes the existing LangGraph workflow externally while leaving the
internal GraphState orchestration unchanged.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from uuid import uuid4

from a2a.types import Message, Part, Role, SendMessageRequest, SendMessageResponse, Task, TaskState, TaskStatus
from google.protobuf.json_format import MessageToDict, ParseDict, ParseError

from .registry import get_agent_card


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


def _extract_text(message: Message) -> str:
    """Extract text input from an A2A SDK Message."""

    text_parts = [part.text for part in message.parts if part.text]
    return "\n".join(text_parts).strip()


def _result_to_text(result: dict[str, Any]) -> str:
    """Render the LangGraph result projection as an agent text response."""

    sections = []
    for key in ("plan", "code", "review", "reflection", "evaluation"):
        value = result.get(key)
        if value:
            sections.append(f"## {key.title()}\n{value}")
    return "\n\n".join(sections) or "Task completed."


def _build_send_message_response(request: SendMessageRequest, final_state: dict[str, Any]) -> SendMessageResponse:
    """Convert the internal LangGraph state into an A2A SDK SendMessageResponse."""

    context_id = request.message.context_id or str(uuid4())
    task_id = request.message.task_id or str(uuid4())
    result = _state_to_external_result(final_state)
    response_message = Message(
        message_id=str(uuid4()),
        context_id=context_id,
        task_id=task_id,
        role=Role.ROLE_AGENT,
        parts=[Part(text=_result_to_text(result), data=result)],
    )
    return SendMessageResponse(
        task=Task(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(
                state=TaskState.TASK_STATE_COMPLETED,
                message=response_message,
            ),
            history=[request.message, response_message],
        )
    )


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
                base_url = f"http://{self.headers.get('Host', '127.0.0.1:8080')}"
                agent_card = MessageToDict(get_agent_card(base_url), preserving_proto_field_name=False)
                self._send_json(200, agent_card)
                return
            self._send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802 - http.server naming convention
            if self.path not in {"/a2a/tasks", "/a2a/message:send"}:
                self._send_json(404, {"error": "Not found"})
                return

            try:
                request = ParseDict(self._read_json_body(), SendMessageRequest())
                task_text = _extract_text(request.message)
                if not task_text:
                    self._send_json(400, {"status": "failed", "error": "SendMessageRequest.message.parts must include text"})
                    return

                final_state = workflow_runner(task_text)
                response = _build_send_message_response(request, final_state)
                self._send_json(200, MessageToDict(response, preserving_proto_field_name=False))
            except ParseError as ex:
                self._send_json(400, {"status": "failed", "error": str(ex)})
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
