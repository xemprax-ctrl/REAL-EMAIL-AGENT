from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.email_agent.gmail_tools import check_inbox, read_email, send_email
from src.email_agent.hitl import FriendlyHumanInTheLoopMiddleware
from src.email_agent.prompts import EMAIL_AGENT_PROMPT

model = ChatOpenAI(model="gpt-5-nano")

agent = create_agent(
    model=model,
    tools=[check_inbox, read_email, send_email],
    system_prompt=EMAIL_AGENT_PROMPT,
    middleware=[
        FriendlyHumanInTheLoopMiddleware(
            interrupt_on={
                "send_email": {
                    "allowed_decisions": [
                        "approve",
                        "edit",
                        "reject",
                        "respond",
                    ],
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