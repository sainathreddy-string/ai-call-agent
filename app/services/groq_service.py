from groq import Groq

from app.config.settings import GROQ_API_KEY


client = Groq(api_key=GROQ_API_KEY)


def transcribe_audio(audio_file_path: str) -> str:
    with open(audio_file_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
        )

    return result.text
