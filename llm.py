import os
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

EMBED_ENDPOINT = "https://api.openai.com/v1/embeddings"
CHAT_ENDPOINT = "https://api.openai.com/v1/chat/completions"


async def get_embedding(text: str) -> list[float]:
    """Return an embedding vector for the given text using the OpenAI embeddings API."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"input": text, "model": EMBED_MODEL}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(EMBED_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]


async def chat_completion(messages: list[dict]) -> str:
    """Send a list of chat messages to the OpenAI chat completions API and return the reply text."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": CHAT_MODEL, "messages": messages}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(CHAT_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
