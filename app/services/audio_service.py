import base64
import wave


def decode_exotel_audio(payload: str) -> bytes:
    return base64.b64decode(payload)


def save_audio_as_wav(audio_chunks: list[bytes], file_path: str) -> None:
    with wave.open(file_path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)

        for chunk in audio_chunks:
            wav_file.writeframes(chunk)
def convert_tts_to_pcm(input_file: str, output_file: str) -> None:
    import subprocess

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            input_file,
            "-ar",
            "8000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            output_file,
        ],
        check=True,
    )