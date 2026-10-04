import asyncio

import edge_tts


VOICE = "en-US-AriaNeural"


async def generate_speech(text: str, output_file: str) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)


def text_to_speech(text: str, output_file: str) -> None:
    asyncio.run(generate_speech(text, output_file))