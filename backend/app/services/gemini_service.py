import json
from typing import AsyncIterator, Union
import httpx
from app.services.ai_provider import AIProvider
from app.config import get_settings

settings = get_settings()

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = httpx.AsyncClient(verify=False, timeout=120)

    def _build_body(self, messages: list[dict], temperature: float, max_tokens: int) -> dict:
        system_parts = []
        contents = []
        for msg in messages:
            role, content = msg["role"], msg["content"]
            if role == "system":
                system_parts.append({"text": content})
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
        body: dict = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system_parts:
            body["systemInstruction"] = {"parts": system_parts}
        return body

    async def generate(
        self,
        messages: list[dict],
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Union[str, AsyncIterator[str]]:
        if stream:
            return self._stream(messages, model, temperature, max_tokens)
        url = f"{_BASE}/{model}:generateContent?key={self.api_key}"
        body = self._build_body(messages, temperature, max_tokens)
        resp = await self.client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _stream(
        self, messages: list[dict], model: str, temperature: float, max_tokens: int
    ) -> AsyncIterator[str]:
        url = f"{_BASE}/{model}:streamGenerateContent?key={self.api_key}&alt=sse"
        body = self._build_body(messages, temperature, max_tokens)
        async with httpx.AsyncClient(verify=False, timeout=120) as client:
            async with client.stream("POST", url, json=body) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if not raw:
                        continue
                    try:
                        chunk = json.loads(raw)
                        text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                        if text:
                            yield text
                    except Exception:
                        continue

    async def get_available_models(self) -> list[dict]:
        return [
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "gemini"},
            {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite", "provider": "gemini"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "gemini"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "gemini"},
        ]
