from groq import Groq

from app.config.settings import GROQ_API_KEY


client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
You are an AI phone call assistant.

Your job is to answer callers clearly, naturally, and briefly.

You are answering calls on behalf of Sainath.

If the caller asks who you are, explain that you are Sainath's AI call assistant.

Do not pretend to be Sainath.

Keep responses suitable for spoken conversation.
"""


def generate_response(user_text: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_text,
            },
        ],
        temperature=0.3,
        max_tokens=100,
    )

    return response.choices[0].message.content
