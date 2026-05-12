# Real Email Agent

LangGraph-based email assistant that can check Gmail, read messages, draft replies, and send outgoing mail only after human approval.

## What this project does

This project combines LangGraph, LangChain, and Gmail API tools to build an email assistant that can:

- check the inbox
- read full email threads
- prepare outgoing messages
- pause before sending and ask for human review

The assistant is designed to help with email work without automatically sending anything unless you approve it.

## Gmail integration

Gmail access is implemented in `src/email_agent/gmail_tools.py`.

It uses:

- `credentials.json` for OAuth client setup
- `token.pickle` to store the authenticated Gmail token locally
- Gmail API scopes that allow reading and sending email

Available Gmail tools:

- `check_inbox(max_results=5)` — lists recent inbox messages
- `read_email(email_id)` — opens a full email by message ID
- `send_email(to, subject, body)` — sends an email through Gmail

## LangGraph

LangGraph runs the agent graph defined in `langgraph.json` and points to `src/email_agent/agent.py`.

The graph wires together:

- the chat model
- the Gmail tools
- the human-in-the-loop middleware

LangGraph is what makes the execution durable and allows the agent to stop, wait for review, and then continue.

## HITL flow

HITL means human-in-the-loop.

When the agent wants to send an email:

1. the model creates a `send_email` tool call
2. `FriendlyHumanInTheLoopMiddleware` intercepts it
3. Studio shows the request for approval or editing
4. you can approve, reject, respond, or edit the tool call
5. the middleware converts the Studio resume value into a Python object and continues execution

This project includes a small wrapper around LangChain’s middleware because Studio sends the resume payload as JSON text.

## Tools

The main tools are in `src/email_agent/gmail_tools.py`.

- `check_inbox` for inbox summaries
- `read_email` for reading a specific message
- `send_email` for outgoing mail

The agent setup in `src/email_agent/agent.py` connects those tools to the model and adds HITL review for `send_email`.

## How to run it

Install dependencies:

```bash
pip install -r requirements.txt
```

Add your environment variables to `.env`, especially your OpenAI key.

Make sure Gmail OAuth files exist locally:

- `credentials.json`
- `token.pickle` will be created after auth

Start LangGraph:

```bash
langgraph dev
```

Then open the LangGraph Studio link and test inbox checking or email sending.

## Push to GitHub

If this is a new local repo, run:

```bash
git init
git add .
git commit -m "Initial email agent"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Important notes

- Do not commit `.env`, `.venv`, `credentials.json`, or `token.pickle`.
- Keep `src/email_agent/hitl.py` if you want the Studio edit flow to keep working.
- If LangChain fixes the HITL JSON parsing in a future release, this wrapper can be simplified later.
