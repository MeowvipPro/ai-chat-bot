from abc import ABC, abstractmethod
from typing import AsyncIterator, Union


class AIProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Union[str, AsyncIterator[str]]:
        pass

    @abstractmethod
    async def get_available_models(self) -> list[dict]:
        pass
