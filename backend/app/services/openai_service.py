from typing import AsyncIterator, Union
import httpx
from openai import AsyncOpenAI
from app.services.ai_provider import AIProvider
from app.config import get_settings

settings = get_settings()


class OpenAIProvider(AIProvider):
    def __init__(self):
        # Use custom httpx client with SSL verification disabled for corporate proxies
        http_client = httpx.AsyncClient(verify=False)
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, http_client=http_client)

    async def generate(
        self,
        messages: list[dict],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Union[str, AsyncIterator[str]]:
        if stream:
            return self._stream(messages, model, temperature, max_tokens)
        else:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

    async def _stream(
        self, messages: list[dict], model: str, temperature: float, max_tokens: int
    ) -> AsyncIterator[str]:
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def get_available_models(self) -> list[dict]:
        return [
            {"id": "gpt-5.4-mini", "name": "GPT-5.4 Mini", "provider": "openai"},
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai"},
        ]
