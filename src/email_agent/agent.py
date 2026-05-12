"""Agent graph setup.

Wires the chat model, Gmail tools, and human-in-the-loop middleware
to create an email assistant that pauses before sending.
"""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.email_agent.gmail_tools import check_inbox, read_email, send_email
from src.email_agent.hitl import FriendlyHumanInTheLoopMiddleware
from src.email_agent.prompts import EMAIL_AGENT_PROMPT

# Initialize the chat model for agentic reasoning
model = ChatOpenAI(model="gpt-5-nano")

# Create the LangGraph agent with tools and HITL middleware.
# The middleware pauses execution when send_email is called and waits for human approval.
agent = create_agent(
    model=model,
    tools=[check_inbox, read_email, send_email],
    system_prompt=EMAIL_AGENT_PROMPT,
    middleware=[
        FriendlyHumanInTheLoopMiddleware(
            interrupt_on={
                # Only send_email requires human approval before execution
                "send_email": {
                    # All decision types are allowed: approve, edit, reject, or respond
                    "allowed_decisions": [
                        "approve",
                        "edit",
                        "reject",
                        "respond",
                    ],
                    # The args_schema tells Studio which fields can be edited
                    "args_schema": send_email.args_schema.model_json_schema(),
                    "description": (
                        "Review this outgoing email before it is sent. "
                        "Use edit to change the recipient, subject, or body."
                    ),
                }
            }
        )
    ],
)