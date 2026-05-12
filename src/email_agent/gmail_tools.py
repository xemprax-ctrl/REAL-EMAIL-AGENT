"""Gmail tools for the email agent.

Provides LangChain tools to check inbox, read emails, and send messages via Gmail API.
"""

import os
import pickle
import base64

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText

# Gmail API scope: allows reading and sending mail
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def gmail_service():
    """Authenticate to Gmail and return the Gmail API service.
    
    Uses token.pickle to cache credentials. If the token is invalid or missing,
    opens an OAuth flow for the user to authorize.
    """
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080, open_browser=True)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


from langchain.tools import tool


@tool
def check_inbox(max_results: int = 5) -> str:
    """Check the user's Gmail inbox and return recent emails."""
    service = gmail_service()

    results = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
        .execute()
    )

    messages = results.get("messages", [])

    if not messages:
        return "No emails found in the inbox."

    email_summaries = []

    for msg in messages:
        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            )
            .execute()
        )

        headers = message.get("payload", {}).get("headers", [])

        from_email = next(
            (h["value"] for h in headers if h["name"] == "From"), "Unknown sender"
        )

        subject = next(
            (h["value"] for h in headers if h["name"] == "Subject"), "No subject"
        )

        date = next(
            (h["value"] for h in headers if h["name"] == "Date"), "Unknown date"
        )

        snippet = message.get("snippet", "")

        email_summaries.append(f"""
Email ID: {msg["id"]}
From: {from_email}
Subject: {subject}
Date: {date}
Snippet: {snippet}
""")

    return "\n---\n".join(email_summaries)


@tool
def read_email(email_id: str) -> str:
    """Read a full Gmail email by its Email ID."""
    service = gmail_service()
    message = (
        service.users()
        .messages()
        .get(userId="me", id=email_id, format="full")
        .execute()
    )

    headers = message.get("payload", {}).get("headers", [])

    from_email = next(
        (h["value"] for h in headers if h["name"] == "From"), "Unknown sender"
    )
    subject = next(
        (h["value"] for h in headers if h["name"] == "Subject"), "No subject"
    )
    date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown date")
    body = extract_email_body(message.get("payload", {}))
    return f"""
from:{from_email}
subject:{subject}
date:{date}

Body:
{body}
"""


def extract_email_body(payload: dict) -> str:
    """Extract plain text body from Gmail message payload."""
    if "parts" in payload:
        for part in payload["parts"]:
            body = extract_email_body(part)
            if body:
                return body

    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using Gmail."""

    service = gmail_service()

    message = MIMEText(body)

    message["to"] = to
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    send_request = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw_message})
        .execute()
    )

    return f"Email sent successfully. Message ID: {send_request['id']}"
