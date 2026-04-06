import httpx
from typing import AsyncGenerator
from .base import BaseLLMProvider
from config import settings
# ─────────────────────────────────────────────────────────────
# Ollama Provider Class
# ─────────────────────────────────────────────────────────────
class OllamaProvider(BaseLLMProvider):

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        # base_url = "http://localhost:11434"
    
    def get_name(self) -> str:
        return "ollama"
    
    def get_cost_per_token(self) -> float:
        return 0.0
    
    async def generate_stream(
        self, 
        prompt: str
    ) -> AsyncGenerator[str, None]:
        chat_url = f"{self.base_url}/api/chat"
        generate_url = f"{self.base_url}/api/generate"

        chat_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": settings.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
            "think": False,
        }
        generate_payload = {
            "model": self.model,
            "prompt": f"{settings.system_prompt}\n\n{prompt}",
            "stream": True,
            "think": False,
        }

        attempted_generate_fallback = False

        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=30.0)) as client:
            for url, payload, parse_mode in (
                (chat_url, chat_payload, "chat"),
                (generate_url, generate_payload, "generate"),
            ):
                try:
                    async with client.stream("POST", url, json=payload) as response:
                        response.raise_for_status()

                        import json

                        async for line in response.aiter_lines():
                            if not line:
                                continue

                            if line.startswith("data:"):
                                json_str = line[5:].strip()
                            else:
                                json_str = line

                            try:
                                data = json.loads(json_str)
                            except json.JSONDecodeError:
                                continue

                            if parse_mode == "chat":
                                content = data.get("message", {}).get("content", "")
                            else:
                                content = data.get("response", "")

                            if content:
                                yield content

                            if data.get("done", False):
                                return
                except httpx.HTTPStatusError as exc:
                    # Older Ollama versions may not support /api/chat.
                    if parse_mode == "chat" and exc.response.status_code == 404:
                        attempted_generate_fallback = True
                        continue
                    raise

        if attempted_generate_fallback:
            raise RuntimeError("Ollama fallback to /api/generate did not produce a response.")
# ─────────────────────────────────────────────────────────────
# Example usage
# ─────────────────────────────────────────────────────────────
# async def main():
#     provider = OllamaProvider()
#     async for token in provider.generate_stream("Hello, world!"):
#         print(token, end="", flush=True)

# asyncio.run(main())
