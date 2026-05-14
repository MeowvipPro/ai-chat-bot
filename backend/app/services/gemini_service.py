from typing import AsyncIterator, Union
import google.generativeai as genai
from app.services.ai_provider import AIProvider
from app.config import get_settings

settings = get_settings()


class GeminiProvider(AIProvider):
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def _convert_messages(self, messages: list[dict]) -> tuple[str | None, list[dict]]:
        system_prompt = None
        gemini_messages = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_prompt = content
            elif role == "user":
                gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [content]})
        return system_prompt, gemini_messages

    async def generate(
        self,
        messages: list[dict],
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Union[str, AsyncIterator[str]]:
        system_prompt, gemini_messages = self._convert_messages(messages)
        model_kwargs = {}
        if system_prompt:
            model_kwargs["system_instruction"] = system_prompt
        client = genai.GenerativeModel(model, **model_kwargs)
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if stream:
            return self._stream(client, gemini_messages, generation_config)
        response = await client.generate_content_async(
            gemini_messages, generation_config=generation_config
        )
        return response.text

    async def _stream(self, client, messages, generation_config) -> AsyncIterator[str]:
        response = await client.generate_content_async(
            messages, generation_config=generation_config, stream=True
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def get_available_models(self) -> list[dict]:
        return [
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "gemini"},
            {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite", "provider": "gemini"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "gemini"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "gemini"},
        ]
