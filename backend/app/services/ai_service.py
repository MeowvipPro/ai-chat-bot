from app.services.ai_provider import AIProvider
from app.services.openai_service import OpenAIProvider
from app.services.huggingface_service import HuggingFaceProvider

_providers: dict[str, AIProvider] = {}


def get_ai_provider(provider_type: str) -> AIProvider:
    if provider_type not in _providers:
        if provider_type == "openai":
            _providers[provider_type] = OpenAIProvider()
        elif provider_type == "huggingface":
            _providers[provider_type] = HuggingFaceProvider()
        elif provider_type == "bedrock":
            from app.services.bedrock_service import BedrockProvider
            _providers[provider_type] = BedrockProvider()
        elif provider_type == "gemini":
            from app.services.gemini_service import GeminiProvider
            _providers[provider_type] = GeminiProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_type}")
    return _providers[provider_type]


async def get_all_available_models() -> list[dict]:
    models = []
    for provider_type in ["openai", "huggingface", "bedrock", "gemini"]:
        try:
            provider = get_ai_provider(provider_type)
            models.extend(await provider.get_available_models())
        except Exception:
            pass
    return models
