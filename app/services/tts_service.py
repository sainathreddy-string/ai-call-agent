import asyncio

import edge_tts


VOICES = {
    "en": "en-US-AriaNeural",
    "te": "te-IN-ShrutiNeural",
    "hi": "hi-IN-SwaraNeural",
}


def get_voice(language: str) -> str:
    """
    Return the Edge TTS voice for the detected language.
    """

    language = (
        language or "en"
    ).lower()

    return VOICES.get(
        language,
        VOICES["en"],
    )


async def generate_speech(
    text: str,
    output_file: str,
    language: str = "en",
) -> None:

    voice = get_voice(
        language
    )

    print(
        "TTS language:",
        language,
    )

    print(
        "TTS voice:",
        voice,
    )

    communicate = edge_tts.Communicate(
        text,
        voice,
    )

    await communicate.save(
        output_file
    )


def text_to_speech(
    text: str,
    output_file: str,
    language: str = "en",
) -> None:

    asyncio.run(
        generate_speech(
            text,
            output_file,
            language,
        )
    )