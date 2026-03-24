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
        # model = "llama3.1:8b"
    
    def get_name(self) -> str:
        return "ollama"
    
    def get_cost_per_token(self) -> float:
        return 0.0
    
    async def generate_stream(
        self, 
        prompt: str
    ) -> AsyncGenerator[str, None]:
        # ─────────────────────────────────────────────────────────
        # Build the API URL
        # ─────────────────────────────────────────────────────────
        url = f"{self.base_url}/api/chat"
        # Example: "http://localhost:11434/api/chat"
        
        # ─────────────────────────────────────────────────────────
        # Prepare request body (OpenAI-compatible format)
        # ─────────────────────────────────────────────────────────
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": True,  # Enable streaming
        }
        
        # ─────────────────────────────────────────────────────────
        # Make async HTTP request
        # ─────────────────────────────────────────────────────────
        async with httpx.AsyncClient(timeout=120.0) as client:
            # httpx.AsyncClient = async HTTP client
            # timeout=120.0 = wait up to 120 seconds
            # async with = auto cleanup
            
            async with client.stream(
                "POST",      # HTTP method
                url,         # URL to call
                json=payload # Request body as JSON
            ) as response:
                # client.stream() = for streaming responses
                # 比 client.post() 更適合串流回應
                
                # Check if request succeeded
                response.raise_for_status()
                # 如果 status code 不是 200-299，會拋出例外
                
                # ─────────────────────────────────────────────────────────
                # Parse streaming JSON lines
                # ─────────────────────────────────────────────────────────
                import json
                async for line in response.aiter_lines():
                    # response.aiter_lines() = iterate over lines in response
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Remove "data:" prefix if present (SSE format)
                    if line.startswith("data:"):
                        json_str = line[5:].strip()
                    else:
                        json_str = line
                    
                    try:
                        data = json.loads(json_str)
                        # data = {"message": {"content": "K"}, "done": False}
                        
                        content = data.get("message", {}).get("content", "")
                        
                        if content:
                            yield content
                        
                        # Check if generation is done
                        if data.get("done", False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
# ─────────────────────────────────────────────────────────────
# Example usage
# ─────────────────────────────────────────────────────────────
# async def main():
#     provider = OllamaProvider()
#     async for token in provider.generate_stream("Hello, world!"):
#         print(token, end="", flush=True)

# asyncio.run(main())