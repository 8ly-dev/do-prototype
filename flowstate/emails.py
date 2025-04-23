"""
Email utilities for the Flowstate application.

This module provides classes and functions for sending emails,
including dataclasses for representing email messages and sender configurations.
"""

import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import flowstate.secrets


@dataclass
class Email:
    """
    Represents an email message.

    Attributes:
        to: The recipient's email address
        subject: The subject of the email
        body: The body text of the email
        from_sender: Optional sender email address (defaults to the SMTP username if not provided)
        cc: Optional comma-separated list of CC recipients
        bcc: Optional comma-separated list of BCC recipients
    """
    to: str
    subject: str
    body: str
    from_sender: str | None = None
    cc: str | None = None
    bcc: str | None = None


@dataclass
class Sender:
    """
    Represents SMTP server configuration for sending emails.

    Attributes:
        server: The SMTP server hostname
        port: The SMTP server port
        username: The username for SMTP authentication
        password: The password for SMTP authentication
    """
    server: str
    port: int
    username: str
    password: str


def send_email(
    email: Email,
    sender: Sender,
):
    """
    Send an email using the specified sender configuration.

    This function creates a MIME message from the Email object and sends it
    using the SMTP server configuration in the Sender object.

    Args:
        email: The Email object containing the message details
        sender: The Sender object containing the SMTP server configuration
    """
    message = MIMEMultipart()
    message["From"] = email.from_sender or sender.username
    message["To"] = email.to
    message["Subject"] = email.subject
    if email.cc:
        message["Cc"] = email.cc
    if email.bcc:
        message["Bcc"] = email.bcc

    message.attach(MIMEText(email.body, "plain"))

    with smtplib.SMTP(sender.server, sender.port) as server:
        server.starttls()
        server.login(sender.username, sender.password)
        recipients = [email.to]
        if email.cc:
            recipients.extend(email.cc.split(","))
        if email.bcc:
            recipients.extend(email.bcc.split(","))

        server.send_message(message, message["From"], recipients)
