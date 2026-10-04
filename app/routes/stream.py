import json
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.audio_service import decode_exotel_audio, save_audio_as_wav
from app.services.groq_service import transcribe_audio

router = APIRouter()


@router.websocket("/stream")
async def stream(websocket: WebSocket):
    await websocket.accept()

    print("Exotel WebSocket connected")

    audio_chunks = []

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            event = data.get("event")

            if event == "connected":
                print("Exotel connection event received")

            elif event == "start":
                audio_chunks = []
                print("Call stream started")

            elif event == "media":
                payload = data.get("media", {}).get("payload")

                if payload:
                    audio_chunks.append(decode_exotel_audio(payload))

            elif event == "stop":
                print("Call stream stopped")

                if audio_chunks:
                    os.makedirs("app/audio", exist_ok=True)

                    file_path = "app/audio/call_audio.wav"

                    save_audio_as_wav(audio_chunks, file_path)

                    print("Audio saved")
                    print("Sending audio to Groq STT...")

                    transcript = transcribe_audio(file_path)

                    print(f"Transcript: {transcript}")

                break

            elif event == "dtmf":
                print("DTMF received:", data.get("dtmf", {}))

    except WebSocketDisconnect:
        print("Exotel WebSocket disconnected")

    except Exception as e:
        print("Stream error:", e)
