from groq import Groq

from app.config.settings import GROQ_API_KEY


client = Groq(
    api_key=GROQ_API_KEY
)


def detect_script_language(
    text: str,
) -> str:
    """
    Detect language from the written script.

    Telugu Unicode range:
        U+0C00 - U+0C7F

    Hindi / Devanagari Unicode range:
        U+0900 - U+097F
    """

    telugu_count = 0
    hindi_count = 0

    for character in text:

        code_point = ord(character)

        if 0x0C00 <= code_point <= 0x0C7F:
            telugu_count += 1

        elif 0x0900 <= code_point <= 0x097F:
            hindi_count += 1

    if telugu_count > hindi_count and telugu_count > 0:
        return "te"

    if hindi_count > telugu_count and hindi_count > 0:
        return "hi"

    return "en"


def transcribe_audio(
    audio_file_path: str,
) -> dict:
    """
    Convert caller speech into text and detect
    the language spoken by the caller.
    """

    with open(
        audio_file_path,
        "rb",
    ) as audio_file:

        result = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            language=None,
            temperature=0.0,
            response_format="verbose_json",
        )

    transcript = result.text.strip()

    # ---------------------------------------------------------
    # Whisper's detected language
    # ---------------------------------------------------------

    whisper_language = getattr(
        result,
        "language",
        None,
    )

    if whisper_language:
        whisper_language = (
            whisper_language.lower()
        )

    # ---------------------------------------------------------
    # Script-based fallback
    # ---------------------------------------------------------

    script_language = detect_script_language(
        transcript
    )

    # ---------------------------------------------------------
    # Decide final language
    # ---------------------------------------------------------

    if script_language in {
        "te",
        "hi",
    }:

        detected_language = (
            script_language
        )

    elif whisper_language in {
        "en",
        "te",
        "hi",
    }:

        detected_language = (
            whisper_language
        )

    else:

        detected_language = "en"

    print(
        "Whisper language:",
        whisper_language,
    )

    print(
        "Script language:",
        script_language,
    )

    print(
        "Detected language:",
        detected_language,
    )

    print(
        "Transcript:",
        transcript,
    )

    return {
        "text": transcript,
        "language": detected_language,
    }