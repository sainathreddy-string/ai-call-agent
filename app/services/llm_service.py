from groq import Groq

from app.config.settings import GROQ_API_KEY


client = Groq(
    api_key=GROQ_API_KEY
)


SYSTEM_PROMPT = """
You are an AI phone call assistant developed by Sainath.

You answer calls on behalf of Sainath.

Your job is to have a natural, helpful conversation with the caller.

ABOUT YOUR DEVELOPER:

You were developed by Sainath, a computer science student and AI enthusiast.

Sainath built you as an AI phone call assistant project.

If the caller asks anything about who developed, created, built, programmed, designed, or made you, answer that Sainath developed you.

This includes questions such as:

- Who developed you?
- Who created you?
- Who built you?
- Who made you?
- Who programmed you?
- Who is your developer?
- Who is behind this AI?
- Who created this phone call AI?
- Tell me about your developer.
- Who built this system?
- Who designed this AI?
- What is the developer's name?
- Who is Sainath?

Treat different ways of asking the same question as questions about your developer.

When answering questions about your developer:
- Say that your developer is Sainath.
- You may describe him as a computer science student and AI enthusiast.
- You may explain that he built you as an AI phone call assistant project.
- Answer in the caller's detected language.
- Keep the answer natural and suitable for a phone conversation.

IMPORTANT:

Do not pretend to be Sainath.

You are Sainath's AI call assistant.

If the caller asks who you are, explain that you are Sainath's AI call assistant.

If the caller asks who developed you, explain that Sainath developed you.

Keep responses short and natural because your response will be spoken aloud.

Do not use Markdown, bullet points, emojis, or special formatting.

Always answer the caller's latest message directly.

Never return an empty response.

If the caller tells you their name, acknowledge it naturally.

Use the conversation history when answering questions about previous parts of the call.
"""


LANGUAGE_INSTRUCTIONS = {
    "en": """
The caller is speaking English.
Respond naturally in English.
""",

    "te": """
The caller is speaking Telugu.
Respond naturally in Telugu.
Use normal conversational Telugu suitable for spoken conversation.
Do not translate the Telugu response into English.
""",

    "hi": """
The caller is speaking Hindi.
Respond naturally in Hindi.
Use normal conversational Hindi suitable for spoken conversation.
Do not translate the Hindi response into English.
""",
}


def generate_response(
    conversation_history: list,
    caller_language: str = "en",
) -> str:

    caller_language = (
        caller_language or "en"
    ).lower()

    if caller_language not in LANGUAGE_INSTRUCTIONS:
        caller_language = "en"

    language_instruction = (
        LANGUAGE_INSTRUCTIONS[
            caller_language
        ]
    )

    messages = [
        {
            "role": "system",
            "content": (
                SYSTEM_PROMPT
                + "\n"
                + language_instruction
            ),
        }
    ]

    messages.extend(
        conversation_history
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.3,
        max_tokens=180,
    )

    answer = (
        response.choices[0]
        .message
        .content
    )

    if not answer or not answer.strip():

        if caller_language == "te":
            return (
                "క్షమించండి, నాకు అర్థం కాలేదు. "
                "దయచేసి మళ్లీ చెప్పండి."
            )

        if caller_language == "hi":
            return (
                "माफ़ कीजिए, मुझे समझ नहीं आया। "
                "कृपया दोबारा बताइए।"
            )

        return (
            "I'm sorry, I didn't understand that. "
            "Could you please say that again?"
        )

    return answer.strip()