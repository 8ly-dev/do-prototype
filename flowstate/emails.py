import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import flowstate.secrets


@dataclass
class Email:
    to: str
    subject: str
    body: str
    from_sender: str | None = None
    cc: str | None = None
    bcc: str | None = None


@dataclass
class Sender:
    server: str
    port: int
    username: str
    password: str


def send_email(
    email: Email,
    sender: Sender,
):
    """Sends an email to the specified address."""
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
