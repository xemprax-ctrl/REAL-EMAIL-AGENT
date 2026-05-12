# HITL Resume JSON Examples

Use these JSON snippets when responding to a Human-in-the-Loop (HITL) review in LangGraph Studio.
Paste the JSON directly into the "Provide a value to resume execution" box (choose the JSON/RAW mode) and click Resume.

Important: Do NOT wrap the entire JSON in extra quotes. Studio sometimes shows strings — the middleware expects unquoted JSON text.

## Approve
Quick accept (no extra fields required):

```json
{"decisions":[{"type":"approve"}]}
```

## Edit
Change the tool call before the agent executes it. Use this when you want to modify the email recipient, subject, or body.

**How to edit:**
1. Replace `recipient@example.com` with the actual recipient email
2. Update `Updated subject` with the real subject line
3. Update `Updated body` with the actual email message
4. Keep the `name` as `send_email` (don't change this)
5. Paste the entire JSON into Studio and click Resume

**Example (CHANGE THE EMAIL AND TEXT):**

```json
{
  "decisions": [
    {
      "type": "edit",
      "edited_action": {
        "name": "send_email",
        "args": {
          "to": "recipient@example.com",
          "subject": "Updated subject",
          "body": "Updated body"
        }
      }
    }
  ]
}
```

## Reject
Decline execution and optionally provide an explanation:

```json
{"decisions":[{"type":"reject","message":"Do not send — needs more context"}]}
```

## Respond
Answer on behalf of the tool (useful for tools that expect a user reply). The tool execution is skipped and a synthetic tool message is returned to the model.

```json
{"decisions":[{"type":"respond","message":"I will reply: Thanks — let's schedule a meeting."}]}
```

## Tips and common pitfalls

- Make sure the `name` in the edited action matches the tool name (e.g., `send_email`).
- `edited_action.args` must match the tool's schema (for `send_email`: `to`, `subject`, `body`).
- Avoid adding stray commas or extra quotes — JSON must be valid and not double-quoted.
- If Studio displays the resume input as a quoted string, copy the inner JSON (without the surrounding quotes) into the box.

If you want, I can add a tiny helper script to validate or pretty-print the JSON before you paste it.
