import httpx
from typing import AsyncGenerator
from .base import BaseLLMProvider
from config import settings
# ─────────────────────────────────────────────────────────────
# Ollama Provider Class
# ─────────────────────────────────────────────────────────────
class OllamaProvider(BaseLLMProvider):
    """
    Ollama local LLM provider
    
    API format:
    POST http://localhost:11434/api/generate
    """
    
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
        url = f"{self.base_url}/api/generate"
        # Example: "http://localhost:11434/api/generate"
        
        # ─────────────────────────────────────────────────────────
        # Prepare request body
        # ─────────────────────────────────────────────────────────
        payload = {
            "model": self.model,
            "prompt": prompt,
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
                # Parse SSE stream
                # ─────────────────────────────────────────────────────────
                async for line in response.aiter_lines():
                    # response.aiter_lines() = iterate over lines in response
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Skip lines starting with ":" (SSE comments)
                    if line.startswith(":"):
                        continue
                    
                    # Parse the JSON
                    # Line format: data: {"response": "K", ...}
                    if line.startswith("data:"):
                        json_str = line[5:].strip()  # Remove "data:" prefix
                        # "data: {"response": "K"}" → '{"response": "K"}'
                        
                        import json
                        try:
                            data = json.loads(json_str)
                            # Convert JSON string to Python dict
                            # '{"response": "K"}' → {"response": "K"}
                            
                            token = data.get("response", "")
                            # Get "response" field / 取得 "response" 欄位
                            # data = {"response": "K", "done": False}
                            # token = "K"
                            
                            if token:
                                yield token
                                # Yield = send to API endpoint
                            
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