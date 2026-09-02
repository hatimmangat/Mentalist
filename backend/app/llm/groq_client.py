import os
import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


class GroqNotConfiguredError(Exception):
    pass


async def generate_response(system_prompt: str, conversation_messages: list, temperature: float = 0.6, max_tokens: int = 700) -> str:
    if not GROQ_API_KEY:
        raise GroqNotConfiguredError(
            "GROQ_API_KEY is not set. Get a free key at console.groq.com and set it "
            "in your environment / .env file."
        )

    messages = [{"role": "system", "content": system_prompt}] + conversation_messages

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
        if resp.status_code >= 400:
            # Surface Groq's actual error body instead of a bare "400 Bad
            # Request" - that body names exactly what's wrong (bad model
            # id, invalid key, malformed request, etc).
            try:
                error_detail = resp.json()
            except Exception:
                error_detail = resp.text
            raise RuntimeError(f"Groq API error ({resp.status_code}): {error_detail}")
        data = resp.json()

    return data["choices"][0]["message"]["content"]