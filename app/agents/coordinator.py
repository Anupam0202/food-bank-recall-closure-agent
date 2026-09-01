from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from app.agents.prompts import SYSTEM_INSTRUCTION
from app.agents.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CoordinatorResult:
    summary: str
    duration_ms: int
    outcome: str
    mode: str


def build_root_agent(model_name: str):
    """Construct the pinned ADK 2.x root agent through its documented public API."""
    try:
        from google.adk import Agent
    except ImportError as exc:
        raise RuntimeError("Install google-adk==2.7.1 for the ADK runtime") from exc
    return Agent(
        name="RecallCoordinatorAgent",
        model=model_name,
        description="Coordinates review-only recommendations for an internal food-recall response.",
        instruction=SYSTEM_INSTRUCTION,
        tools=ALL_TOOLS,
    )


class AdkCoordinator:
    def __init__(self, mode: str, model_name: str) -> None:
        self.mode = mode.lower()
        self.model_name = model_name
        self.agent = build_root_agent(model_name) if self.mode == "live" else None

    async def summarize(self, incident: dict[str, Any], matches: list[dict[str, Any]], tasks: list[dict[str, Any]] | None = None) -> CoordinatorResult:
        start = perf_counter()
        if self.mode in {"mock", "replay"}:
            exact = sum(1 for match in matches if match.get("category") == "EXACT_MATCH")
            review = sum(1 for match in matches if match.get("category") in {"IDENTIFIER_REVIEW", "SEMANTIC_OR_VISUAL_REVIEW", "INSUFFICIENT_DATA"})
            prefix = "MOCK_GEMINI" if self.mode == "mock" else "REPLAY"
            summary = f"[{prefix}] Coordinator proposed {exact} reversible quarantine hold(s) and {review} human review(s)."
            return CoordinatorResult(summary, int((perf_counter() - start) * 1000), "mocked" if self.mode == "mock" else "replayed", self.mode)

        try:
            from google.adk.runners import InMemoryRunner
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Pinned ADK runner dependencies are unavailable") from exc

        runner = InMemoryRunner(agent=self.agent, app_name="recall_closure")
        user_id = "system"
        session_id = incident["id"]
        await runner.session_service.create_session(app_name="recall_closure", user_id=user_id, session_id=session_id)
        safe_context = {"incident": incident, "matches": matches, "tasks": tasks or []}
        message = types.Content(role="user", parts=[types.Part(text=json.dumps(safe_context, ensure_ascii=False))])
        final_text = ""
        try:
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
                is_final = getattr(event, "is_final_response", None)
                if callable(is_final) and not is_final():
                    continue
                content = getattr(event, "content", None)
                for part in getattr(content, "parts", []) if content else []:
                    text = getattr(part, "text", None)
                    if text:
                        final_text += text
            outcome = "success"
            return CoordinatorResult(final_text.strip() or "Coordinator completed without a text summary.", int((perf_counter() - start) * 1000), outcome, self.mode)
        except Exception:
            logger.exception("ADK coordinator call failed", extra={"event_type": "model_call", "tool_name": "RecallCoordinatorAgent", "outcome": "error"})
            raise
