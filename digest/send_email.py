"""Sends the digest via Gmail SMTP. Credentials come from environment
variables (GitHub Actions Secrets in production; a local .env for testing).
Never hardcode credentials in this file.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_digest_email(html_body: str, subject: str = None) -> None:
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("DIGEST_RECIPIENT", sender)
    subject = subject or "Daily Market Digest"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, recipient, msg.as_string())
