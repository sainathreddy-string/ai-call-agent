from datetime import datetime
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


def create_call_record(
    stream_sid: str,
    call_sid: str,
    caller_number: str,
    called_number: str,
) -> dict:

    start_time = datetime.now(IST)

    return {
        "stream_sid": stream_sid,
        "call_sid": call_sid,
        "caller_number": caller_number,
        "called_number": called_number,
        "start_time": start_time,
        "end_time": None,
        "duration_seconds": None,
        "conversation": [],
    }


def add_conversation_turn(
    call_record: dict,
    speaker: str,
    text: str,
    language: str,
) -> None:

    call_record["conversation"].append(
        {
            "speaker": speaker,
            "text": text,
            "language": language,
            "timestamp": datetime.now(IST),
        }
    )


def finish_call(
    call_record: dict,
) -> dict:

    end_time = datetime.now(IST)

    call_record["end_time"] = end_time

    start_time = call_record["start_time"]

    duration = (
        end_time - start_time
    ).total_seconds()

    call_record[
        "duration_seconds"
    ] = round(duration, 2)

    return call_record