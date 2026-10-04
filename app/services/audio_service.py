import base64
import subprocess
import wave


def decode_exotel_audio(
    payload: str,
) -> bytes:
    return base64.b64decode(payload)


def save_audio_as_wav(
    audio_chunks: list[bytes],
    file_path: str,
) -> None:

    with wave.open(
        file_path,
        "wb",
    ) as wav_file:

        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)

        for chunk in audio_chunks:
            wav_file.writeframes(chunk)


def convert_tts_to_pcm(
    input_file: str,
    output_file: str,
) -> None:

    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vn",
        "-ar",
        "8000",
        "-ac",
        "1",
        "-f",
        "s16le",
        "-c:a",
        "pcm_s16le",
        output_file,
    ]

    print(
        "Running FFmpeg:",
        " ".join(command),
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:

        print(
            "FFmpeg return code:",
            result.returncode,
        )

        print(
            "FFmpeg stderr:",
            result.stderr,
        )

        raise RuntimeError(
            "FFmpeg failed to convert TTS audio."
        )


def read_pcm_audio(
    file_path: str,
) -> bytes:

    with open(
        file_path,
        "rb",
    ) as audio_file:

        return audio_file.read()