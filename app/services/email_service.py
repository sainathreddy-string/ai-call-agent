import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email(
    subject: str,
    body: str,
) -> None:

    if not GMAIL_ADDRESS:
        raise ValueError(
            "GMAIL_ADDRESS is missing from .env"
        )

    if not GMAIL_APP_PASSWORD:
        raise ValueError(
            "GMAIL_APP_PASSWORD is missing from .env"
        )

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = GMAIL_ADDRESS
    message["To"] = GMAIL_ADDRESS

    message.set_content(body)

    with smtplib.SMTP(
        "smtp.gmail.com",
        587,
    ) as smtp:

        smtp.starttls()

        smtp.login(
            GMAIL_ADDRESS,
            GMAIL_APP_PASSWORD,
        )

        smtp.send_message(message)

    print(
        "Email sent successfully."
    )


def build_call_report(
    call_record: dict,
) -> str:

    start_time = call_record["start_time"]
    end_time = call_record["end_time"]
    duration = call_record["duration_seconds"]

    lines = []

    lines.append(
        "AI CALL AGENT - CALL REPORT"
    )

    lines.append(
        "=" * 50
    )

    lines.append("")

    lines.append(
        f"Caller number: "
        f"{call_record['caller_number']}"
    )

    lines.append(
        f"Called number: "
        f"{call_record['called_number']}"
    )

    lines.append(
        f"Call SID: "
        f"{call_record['call_sid']}"
    )

    lines.append(
        f"Stream SID: "
        f"{call_record['stream_sid']}"
    )

    lines.append(
        f"Start time: "
        f"{start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )

    lines.append(
        f"End time: "
        f"{end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )

    lines.append(
        f"Duration: "
        f"{duration} seconds"
    )

    lines.append("")

    lines.append(
        "CONVERSATION"
    )

    lines.append(
        "=" * 50
    )

    for index, turn in enumerate(
        call_record["conversation"],
        start=1,
    ):

        speaker = turn["speaker"].upper()
        language = turn["language"]
        text = turn["text"]

        lines.append(
            f"{index}. {speaker} [{language}]"
        )

        lines.append(
            text
        )

        lines.append("")

    return "\n".join(lines)


def send_call_report(
    call_record: dict,
) -> None:

    report = build_call_report(
        call_record
    )

    subject = (
        "AI Call Agent - "
        f"Call Report - "
        f"{call_record['caller_number']}"
    )

    send_email(
        subject,
        report,
    )