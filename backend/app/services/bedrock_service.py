import json
from typing import AsyncIterator, Union
import boto3
from app.services.ai_provider import AIProvider
from app.config import get_settings

settings = get_settings()


class BedrockProvider(AIProvider):
    def __init__(self):
        session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_REGION,
        )
        self.client = session.client("bedrock-runtime")
        self.model_id = settings.BEDROCK_MODEL_ID

    async def generate(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Union[str, AsyncIterator[str]]:
        model_id = model or self.model_id

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": self._convert_messages(messages),
        }

        # Extract system message if present
        system_msg = self._extract_system(messages)
        if system_msg:
            body["system"] = system_msg

        if stream:
            return self._stream(model_id, body)
        else:
            response = self.client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            result = json.loads(response["body"].read())
            return result["content"][0]["text"]

    def _extract_system(self, messages: list[dict]) -> str | None:
        for msg in messages:
            if msg.get("role") == "system":
                return msg["content"]
        return None

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
            if msg.get("role") != "system"
        ]

    async def _stream(
        self, model_id: str, body: dict
    ) -> AsyncIterator[str]:
        response = self.client.invoke_model_with_response_stream(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk["type"] == "content_block_delta":
                yield chunk["delta"].get("text", "")

    async def get_available_models(self) -> list[dict]:
        return [
            {
                "id": self.model_id,
                "name": "Claude Sonnet 4 (Bedrock)",
                "provider": "bedrock",
            },
        ]
