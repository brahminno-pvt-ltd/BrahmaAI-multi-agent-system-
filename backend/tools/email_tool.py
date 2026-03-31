"""
BrahmaAI Email Simulation Tool
Mock email sending for demo/development.
"""

import logging
import time
import uuid
from typing import Any

from backend.tools.registry import BaseTool

logger = logging.getLogger(__name__)


class EmailTool(BaseTool):
    name = "email_tool"
    description = "Send emails (simulation/mock — connect real SMTP in production)"
    args = {
        "to": "str: Recipient email address",
        "subject": "str: Email subject",
        "body": "str: Email body content",
        "cc": "str: CC recipients (optional)",
    }

    _sent_emails: list[dict[str, Any]] = []

    async def execute(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        logger.info(f"[EmailTool] Sending email to: {to}")

        email_record = {
            "id": str(uuid.uuid4()),
            "to": to,
            "cc": cc,
            "subject": subject,
            "body": body,
            "sent_at": time.time(),
            "status": "sent",
        }
        self._sent_emails.append(email_record)

        return {
            "status": "success",
            "email_id": email_record["id"],
            "output": (
                f"✅ Email sent successfully!\n"
                f"To: {to}\n"
                f"Subject: {subject}\n"
                f"Body preview: {body[:200]}...\n"
                f"(Note: This is a simulation. Connect SMTP for real sending.)"
            ),
            "record": email_record,
        }

    @classmethod
    def get_sent_emails(cls) -> list[dict[str, Any]]:
        return cls._sent_emails
