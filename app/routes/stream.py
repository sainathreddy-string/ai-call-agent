import asyncio
import base64
import json
import os
import uuid
import wave

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.audio_service import (
    convert_tts_to_pcm,
    decode_exotel_audio,
    read_pcm_audio,
)

from app.services.call_service import (
    add_conversation_turn,
    create_call_record,
    finish_call,
)

from app.services.groq_service import transcribe_audio
from app.services.llm_service import generate_response
from app.services.tts_service import text_to_speech
from app.services.email_service import send_call_report


router = APIRouter()


SAMPLE_RATE = 8000
SILENCE_DURATION = 0.8
SPEECH_THRESHOLD = 500
CHUNK_SIZE = 3200


def is_speech(audio_data: bytes) -> bool:

    if not audio_data:
        return False

    samples = []

    for i in range(
        0,
        len(audio_data) - 1,
        2,
    ):

        sample = int.from_bytes(
            audio_data[i:i + 2],
            byteorder="little",
            signed=True,
        )

        samples.append(
            abs(sample)
        )

    if not samples:
        return False

    average_volume = (
        sum(samples) / len(samples)
    )

    return (
        average_volume
        > SPEECH_THRESHOLD
    )


def save_pcm_as_wav(
    audio_data: bytes,
    file_path: str,
) -> None:

    with wave.open(
        file_path,
        "wb",
    ) as wav_file:

        wav_file.setnchannels(1)

        wav_file.setsampwidth(2)

        wav_file.setframerate(
            SAMPLE_RATE
        )

        wav_file.writeframes(
            audio_data
        )


async def send_tts(
    websocket: WebSocket,
    stream_sid: str,
    text: str,
    language: str = "en",
) -> None:

    print(
        "Generating TTS:",
        text,
    )

    print(
        "TTS language:",
        language,
    )

    mp3_file = (
        f"/tmp/tts_{uuid.uuid4().hex}.mp3"
    )

    pcm_file = (
        f"/tmp/tts_{uuid.uuid4().hex}.pcm"
    )

    try:

        await asyncio.to_thread(
            text_to_speech,
            text,
            mp3_file,
            language,
        )

        await asyncio.to_thread(
            convert_tts_to_pcm,
            mp3_file,
            pcm_file,
        )

        pcm_audio = await asyncio.to_thread(
            read_pcm_audio,
            pcm_file,
        )

        print(
            "TTS PCM audio size:",
            len(pcm_audio),
            "bytes",
        )

        chunks = [
            pcm_audio[i:i + CHUNK_SIZE]
            for i in range(
                0,
                len(pcm_audio),
                CHUNK_SIZE,
            )
        ]

        print(
            "TTS chunks to send:",
            len(chunks),
        )

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            payload = (
                base64.b64encode(
                    chunk
                ).decode("utf-8")
            )

            message = {
                "event": "media",
                "stream_sid": stream_sid,
                "media": {
                    "payload": payload,
                },
            }

            await websocket.send_text(
                json.dumps(message)
            )

            print(
                "TTS audio chunk sent:",
                index,
                "/",
                len(chunks),
                "-",
                len(chunk),
                "bytes",
            )

            chunk_duration = (
                len(chunk)
                / (SAMPLE_RATE * 2)
            )

            await asyncio.sleep(
                chunk_duration
            )

        print(
            "Finished sending TTS. Total chunks:",
            len(chunks),
        )

        mark_message = {
            "event": "mark",
            "stream_sid": stream_sid,
            "mark": {
                "name": "tts_complete",
            },
        }

        await websocket.send_text(
            json.dumps(mark_message)
        )

        print(
            "TTS completion mark sent."
        )

    finally:

        for file_path in (
            mp3_file,
            pcm_file,
        ):

            try:

                if os.path.exists(
                    file_path
                ):

                    os.remove(
                        file_path
                    )

            except Exception:
                pass


async def process_speech(
    websocket: WebSocket,
    stream_sid: str,
    audio_data: bytes,
    conversation_history: list,
    call_record: dict,
) -> None:

    print(
        "Processing caller speech..."
    )

    wav_file = (
        f"/tmp/caller_{uuid.uuid4().hex}.wav"
    )

    try:

        save_pcm_as_wav(
            audio_data,
            wav_file,
        )

        print(
            "Audio size:",
            len(audio_data),
            "bytes",
        )

        print(
            "Sending audio to Groq Whisper..."
        )

        transcription = await asyncio.to_thread(
            transcribe_audio,
            wav_file,
        )

        transcript = (
            transcription["text"]
            .strip()
        )

        caller_language = (
            transcription["language"]
        )

        print(
            "Caller language:",
            caller_language,
        )

        print(
            "Caller transcript:",
            transcript,
        )

        if not transcript:

            print(
                "Empty transcript. Ignoring."
            )

            return

        # ---------------------------------------------
        # Save caller's message
        # ---------------------------------------------

        add_conversation_turn(
            call_record,
            "caller",
            transcript,
            caller_language,
        )

        # ---------------------------------------------
        # LLM conversation history
        # ---------------------------------------------

        conversation_history.append(
            {
                "role": "user",
                "content": transcript,
            }
        )

        print(
            "Generating AI response..."
        )

        response = await asyncio.to_thread(
            generate_response,
            conversation_history,
            caller_language,
        )

        print(
            "AI response:",
            response,
        )

        # ---------------------------------------------
        # Detect language of AI response
        # ---------------------------------------------

        response_language = "en"

        if any(
            "\u0C00" <= character <= "\u0C7F"
            for character in response
        ):

            response_language = "te"

        elif any(
            "\u0900" <= character <= "\u097F"
            for character in response
        ):

            response_language = "hi"

        # ---------------------------------------------
        # Save AI response
        # ---------------------------------------------

        add_conversation_turn(
            call_record,
            "ai",
            response,
            response_language,
        )

        conversation_history.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        print(
            "Sending AI response using language:",
            response_language,
        )

        await send_tts(
            websocket,
            stream_sid,
            response,
            response_language,
        )

    except Exception as error:

        print(
            "Speech processing error:",
            error,
        )

    finally:

        try:

            if os.path.exists(
                wav_file
            ):

                os.remove(
                    wav_file
                )

        except Exception:
            pass


@router.websocket("/stream")
async def stream(
    websocket: WebSocket,
):

    await websocket.accept()

    print(
        "Exotel WebSocket connected"
    )

    stream_sid = None
    call_record = None
    audio_buffer = bytearray()
    conversation_history = []
    speech_active = False
    silence_start = None
    ai_busy = True
    processing_task = None

    try:

        while True:

            message = (
                await websocket.receive_text()
            )

            data = json.loads(
                message
            )

            event = data.get(
                "event"
            )

            # ---------------------------------------------
            # Connected
            # ---------------------------------------------

            if event == "connected":

                print(
                    "Exotel connection event received"
                )

            # ---------------------------------------------
            # Start
            # ---------------------------------------------

            elif event == "start":

                start_data = data.get(
                    "start",
                    {},
                )

                stream_sid = (
                    start_data.get(
                        "stream_sid"
                    )
                )

                call_sid = (
                    start_data.get(
                        "call_sid"
                    )
                )

                caller_number = (
                    start_data.get(
                        "from"
                    )
                )

                called_number = (
                    start_data.get(
                        "to"
                    )
                )

                print(
                    "Call stream started"
                )

                print(
                    "Stream SID:",
                    stream_sid,
                )

                print(
                    "Call SID:",
                    call_sid,
                )

                print(
                    "Caller:",
                    caller_number,
                )

                print(
                    "Called number:",
                    called_number,
                )

                print(
                    "Media format:",
                    start_data.get(
                        "media_format"
                    ),
                )

                # -----------------------------------------
                # Create call record
                # -----------------------------------------

                call_record = (
                    create_call_record(
                        stream_sid,
                        call_sid,
                        caller_number,
                        called_number,
                    )
                )

                print(
                    "Call record created."
                )

                # -----------------------------------------
                # Greeting
                # -----------------------------------------

                greeting = (
                    "Hello, this is an AI call "
                    "assistant developed by Sainath. "
                    "How can I help you?"
                )

                ai_busy = True

                # Save greeting in call record

                add_conversation_turn(
                    call_record,
                    "ai",
                    greeting,
                    "en",
                )

                # Save greeting in LLM history

                conversation_history.append(
                    {
                        "role": "assistant",
                        "content": greeting,
                    }
                )

                await send_tts(
                    websocket,
                    stream_sid,
                    greeting,
                    "en",
                )

            # ---------------------------------------------
            # Media
            # ---------------------------------------------

            elif event == "media":

                if ai_busy:
                    continue

                media = data.get(
                    "media",
                    {},
                )

                payload = media.get(
                    "payload"
                )

                if not payload:
                    continue

                audio_chunk = (
                    decode_exotel_audio(
                        payload
                    )
                )

                if is_speech(
                    audio_chunk
                ):

                    if not speech_active:

                        speech_active = True

                        print(
                            "Speech started"
                        )

                    audio_buffer.extend(
                        audio_chunk
                    )

                    silence_start = None

                else:

                    if speech_active:

                        audio_buffer.extend(
                            audio_chunk
                        )

                        if (
                            silence_start
                            is None
                        ):

                            silence_start = (
                                asyncio
                                .get_running_loop()
                                .time()
                            )

                        else:

                            silence_duration = (
                                asyncio
                                .get_running_loop()
                                .time()
                                - silence_start
                            )

                            if (
                                silence_duration
                                >= SILENCE_DURATION
                            ):

                                speech_active = False
                                silence_start = None

                                print(
                                    "Speech ended."
                                )

                                speech_audio = (
                                    bytes(
                                        audio_buffer
                                    )
                                )

                                audio_buffer.clear()

                                if (
                                    processing_task
                                    is None
                                    or processing_task.done()
                                ):

                                    processing_task = (
                                        asyncio.create_task(
                                            process_speech(
                                                websocket,
                                                stream_sid,
                                                speech_audio,
                                                conversation_history,
                                                call_record,
                                            )
                                        )
                                    )

                                    ai_busy = True

            # ---------------------------------------------
            # Mark
            # ---------------------------------------------

            elif event == "mark":

                mark_data = data.get(
                    "mark",
                    {},
                )

                mark_name = (
                    mark_data.get(
                        "name"
                    )
                )

                print(
                    "Mark received:",
                    mark_name,
                )

                if (
                    mark_name
                    == "tts_complete"
                ):

                    print(
                        "Exotel finished TTS playback."
                    )

                    ai_busy = False

                    print(
                        "AI is ready for caller speech."
                    )

            # ---------------------------------------------
            # Stop
            # ---------------------------------------------

            elif event == "stop":

                print(
                    "Call stream stopped"
                )

                break

    except WebSocketDisconnect:

        print(
            "Exotel WebSocket disconnected"
        )

    except Exception as error:

        print(
            "WebSocket error:",
            error,
        )

    finally:

        # ---------------------------------------------
        # Finish call record
        # ---------------------------------------------

        if call_record is not None:

            finished_record = finish_call(
                call_record
            )

            print(
                "CALL RECORD:"
            )

            print(
                "Caller:",
                finished_record[
                    "caller_number"
                ],
            )

            print(
                "Duration:",
                finished_record[
                    "duration_seconds"
                ],
                "seconds",
            )

            print(
                "Conversation turns:",
                len(
                    finished_record[
                        "conversation"
                    ]
                ),
            )

            # -----------------------------------------
            # Print full conversation
            # -----------------------------------------

            print(
                "FULL CONVERSATION:"
            )

            for turn in finished_record[
                "conversation"
            ]:

                print(
                    f'{turn["speaker"].upper()} '
                    f'[{turn["language"]}]: '
                    f'{turn["text"]}'
                )

            # -----------------------------------------
            # Send email report
            # -----------------------------------------

            print(
                "Sending call report by email..."
            )

            try:

                send_call_report(
                    finished_record
                )

            except Exception as error:

                print(
                    "Failed to send call report:",
                    error,
                )

        print(
            "WebSocket handler finished."
        )