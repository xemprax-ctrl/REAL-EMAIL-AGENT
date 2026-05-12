"""Human-in-the-loop middleware with Studio JSON resume support.

LangChain's HumanInTheLoopMiddleware expects resume payloads as Python dicts,
but Studio sends them as JSON strings. This wrapper parses the JSON before
the parent middleware processes it, fixing the "string indices must be integers"
error and enabling the edit workflow.

Once LangChain fixes this upstream, this wrapper can be removed.
"""

from __future__ import annotations

import json
from typing import Any

from langchain.agents.middleware.human_in_the_loop import (
    HITLRequest,
    HumanInTheLoopMiddleware,
)
from langchain.agents.middleware.types import AgentState, ContextT, ResponseT, StateT
from langchain_core.messages import AIMessage, ToolCall, ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import interrupt


class FriendlyHumanInTheLoopMiddleware(
    HumanInTheLoopMiddleware[StateT, ContextT, ResponseT]
):
    """Extended HITL middleware that handles JSON string resume payloads from Studio."""

    def after_model(
        self, state: AgentState[Any], runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        messages = state["messages"]
        if not messages:
            return None

        last_ai_msg = next(
            (msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None
        )
        if not last_ai_msg or not last_ai_msg.tool_calls:
            return None

        action_requests: list[dict[str, Any]] = []
        review_configs: list[dict[str, Any]] = []
        interrupt_indices: list[int] = []

        for idx, tool_call in enumerate(last_ai_msg.tool_calls):
            if (config := self.interrupt_on.get(tool_call["name"])) is not None:
                action_request, review_config = self._create_action_and_config(
                    tool_call, config, state, runtime
                )
                action_requests.append(action_request)
                review_configs.append(review_config)
                interrupt_indices.append(idx)

        if not action_requests:
            return None

        hitl_request = HITLRequest(
            action_requests=action_requests,
            review_configs=review_configs,
        )

        raw_response = interrupt(hitl_request)

        if isinstance(raw_response, str):
            raw_response = raw_response.strip().strip('"')
            try:
                raw_response = json.loads(raw_response)
            except json.JSONDecodeError as exc:
                msg = (
                    f"Invalid JSON received: {repr(raw_response[:100])}. "
                    "Resume value must be a JSON object with a `decisions` list.\n\n"
                    "Copy and paste this exact template:\n"
                    '{"decisions":[{"type":"edit","edited_action":{"name":"send_email","args":{"to":"xemprax@gmail.com","subject":"Test Subject","body":"Test Message"}}}]}'
                )
                raise ValueError(msg) from exc

        if not isinstance(raw_response, dict):
            msg = (
                f"Resume value has unexpected type {type(raw_response).__name__}: {repr(raw_response)}. "
                "Expected a JSON object with a `decisions` list."
            )
            raise ValueError(msg)

        decisions = raw_response.get("decisions")
        if not isinstance(decisions, list):
            raise ValueError(
                f"Resume value must include a `decisions` list. Got: {repr(raw_response)}"
            )

        if len(decisions) != len(interrupt_indices):
            msg = (
                f"Number of human decisions ({len(decisions)}) does not match "
                f"number of hanging tool calls ({len(interrupt_indices)})."
            )
            raise ValueError(msg)

        # Apply the human's decisions: approve, reject, respond, or edit each tool call
        revised_tool_calls: list[ToolCall] = []
        artificial_tool_messages: list[ToolMessage] = []
        decision_idx = 0

        for idx, tool_call in enumerate(last_ai_msg.tool_calls):
            if idx in interrupt_indices:
                config = self.interrupt_on[tool_call["name"]]
                decision = decisions[decision_idx]
                decision_idx += 1

                # Process the decision and get back the revised tool call
                # (or None if rejected) and optional synthetic tool message
                revised_tool_call, tool_message = self._process_decision(
                    decision, tool_call, config
                )
                if revised_tool_call is not None:
                    revised_tool_calls.append(revised_tool_call)
                if tool_message:
                    artificial_tool_messages.append(tool_message)
            else:
                revised_tool_calls.append(tool_call)

        last_ai_msg.tool_calls = revised_tool_calls

        return {"messages": [last_ai_msg, *artificial_tool_messages]}
