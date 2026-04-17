import asyncio
import os
from typing import AsyncIterator, Union
from app.services.ai_provider import AIProvider
from app.config import get_settings

settings = get_settings()

# Small models suitable for CPU-only inference (16GB RAM)
CPU_FRIENDLY_MODELS = {
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0": "TinyLlama 1.1B Chat",
    "microsoft/phi-2": "Phi-2 (2.7B)",
    "Qwen/Qwen2-0.5B-Instruct": "Qwen2 0.5B Instruct",
}


class HuggingFaceProvider(AIProvider):
    _tokenizer = None
    _model = None
    _model_name = None

    @classmethod
    def _load_model(cls, model_name: str):
        if cls._model is None or cls._model_name != model_name:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            cls._tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=settings.HF_MODELS_DIR,
                trust_remote_code=True,
            )
            if cls._tokenizer.pad_token is None:
                cls._tokenizer.pad_token = cls._tokenizer.eos_token

            cls._model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir=settings.HF_MODELS_DIR,
                torch_dtype=torch.float32,
                device_map=None,  # explicit CPU, no offloading
                trust_remote_code=True,
            )
            cls._model.eval()
            cls._model_name = model_name
        return cls._tokenizer, cls._model

    def _format_messages(self, messages: list[dict]) -> str:
        """Format messages for chat models using their chat template if available."""
        tokenizer, _ = self._load_model(self._resolve_model(""))
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            # Fallback to manual formatting
            formatted = ""
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    formatted += f"<|system|>\n{content}</s>\n"
                elif role == "user":
                    formatted += f"<|user|>\n{content}</s>\n"
                elif role == "assistant":
                    formatted += f"<|assistant|>\n{content}</s>\n"
            formatted += "<|assistant|>\n"
            return formatted

    def _resolve_model(self, model: str) -> str:
        return model if model else settings.HF_MODEL_NAME

    async def generate(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 512,
        stream: bool = False,
    ) -> Union[str, AsyncIterator[str]]:
        model_name = self._resolve_model(model)

        if stream:
            return self._stream(messages, model_name, temperature, max_tokens)
        else:
            return await self._generate_full(messages, model_name, temperature, max_tokens)

    async def _generate_full(
        self, messages: list[dict], model_name: str, temperature: float, max_tokens: int
    ) -> str:
        import torch
        loop = asyncio.get_event_loop()

        def _run():
            tokenizer, model = self._load_model(model_name)
            prompt = self._format_messages(messages)
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature if temperature > 0 else 1.0,
                    do_sample=temperature > 0,
                    top_p=0.9,
                    repetition_penalty=1.1,
                )
            new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
            return tokenizer.decode(new_tokens, skip_special_tokens=True)

        return await loop.run_in_executor(None, _run)

    async def _stream(
        self, messages: list[dict], model_name: str, temperature: float, max_tokens: int
    ) -> AsyncIterator[str]:
        import torch
        from transformers import TextIteratorStreamer
        from threading import Thread

        tokenizer, model = self._load_model(model_name)
        prompt = self._format_messages(messages)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)

        # Build stop token IDs (eos + chat markers)
        stop_ids = [tokenizer.eos_token_id]
        for marker in ["<|im_end|>", "<|endoftext|>"]:
            token_id = tokenizer.convert_tokens_to_ids(marker)
            if token_id != tokenizer.unk_token_id and token_id not in stop_ids:
                stop_ids.append(token_id)

        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

        generation_kwargs = {
            **inputs,
            "max_new_tokens": max_tokens,
            "temperature": temperature if temperature > 0 else 1.0,
            "do_sample": temperature > 0,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
            "eos_token_id": stop_ids,
            "streamer": streamer,
        }

        thread = Thread(target=lambda: _generate_in_thread(model, generation_kwargs))
        thread.start()

        # Filter out chat template markers that leak through skip_special_tokens
        stop_markers = {"<|im_end|>", "<|im_start|>", "<|endoftext|>", "</s>", "<s>"}
        for token_text in streamer:
            if token_text:
                # Strip any stop markers from the token
                cleaned = token_text
                for marker in stop_markers:
                    cleaned = cleaned.replace(marker, "")
                if cleaned:
                    yield cleaned
            await asyncio.sleep(0)

        thread.join()

    async def get_available_models(self) -> list[dict]:
        models = []
        for model_id, name in CPU_FRIENDLY_MODELS.items():
            models.append({"id": model_id, "name": name, "provider": "huggingface"})
        # Also include the configured model if not in the default list
        if settings.HF_MODEL_NAME not in CPU_FRIENDLY_MODELS:
            models.insert(0, {
                "id": settings.HF_MODEL_NAME,
                "name": settings.HF_MODEL_NAME.split("/")[-1],
                "provider": "huggingface",
            })
        return models


def _generate_in_thread(model, kwargs):
    import torch
    with torch.no_grad():
        model.generate(**kwargs)
