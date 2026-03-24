import httpx
from typing import AsyncGenerator
from .base import BaseLLMProvider
from config import settings
# ─────────────────────────────────────────────────────────────
# Groq Provider Class
# ─────────────────────────────────────────────────────────────
class GroqProvider(BaseLLMProvider):
    """
    Groq cloud LLM provider

    API format:
    POST https://api.groq.com/openai/v1/chat/completions
    Headers: Authorization: Bearer <API_KEY>
    """
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.base_url = "https://api.groq.com/openai/v1"
    
    def get_name(self) -> str:
        """
        Get provider name
        """
        return "groq"
    
    def get_cost_per_token(self) -> float:
        """
        Get cost per token
        Returns:
            float: Cost per 1K tokens
            llama-3.3-70b-specdec = $0.00 (free tier)
        """
        return 0.0  # Free tier for now
    
    async def generate_stream(
        self, 
        prompt: str
    ) -> AsyncGenerator[str, None]:
        """
        Generate response with streaming
        
        Response: Server-Sent Events (SSE)
        每個 chunk 長這樣：
        data: {"choices": [{"delta": {"content": "K"}}]}
        data: {"choices": [{"delta": {"content": "D"}}]}
        data: {"choices": [{"delta": {"content": "AI"}}]}
        Args:
            prompt: The input prompt

        Yields:
            str: Response tokens, one by one / 回應的 token,逐字產生
        """
        # ─────────────────────────────────────────────────────────
        # Build the API URL
        # ─────────────────────────────────────────────────────────
        url = f"{self.base_url}/chat/completions"
        
        # ─────────────────────────────────────────────────────────
        # Prepare request body
        # ─────────────────────────────────────────────────────────
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": settings.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
        }
        
        # ─────────────────────────────────────────────────────────
        # Prepare headers
        # ─────────────────────────────────────────────────────────
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # ─────────────────────────────────────────────────────────
        # Make async HTTP request
        # ─────────────────────────────────────────────────────────
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                url,
                json=payload,
                headers=headers
            ) as response:
                # Check if request succeeded
                response.raise_for_status()
                
                # ─────────────────────────────────────────────────────────
                # Parse SSE stream
                # ─────────────────────────────────────────────────────────
                async for line in response.aiter_lines():
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Skip lines starting with ":" (SSE comments)
                    if line.startswith(":"):
                        continue
                    
                    # Parse the JSON
                    if line.startswith("data:"):
                        json_str = line[5:].strip() # Remove "data:" prefix and whitespace
                        
                        # Check for [DONE]
                        if json_str == "[DONE]":
                            break
                        
                        import json
                        try:
                            data = json.loads(json_str)
                            # Extract content from OpenAI format
                            # data = {"choices": [{"delta": {"content": "K"}}]}
                            choices = data.get("choices", []) #.get for safety. return [] if "choices" not in data 
                            if choices:
                                delta = choices[0].get("delta", {}) # choices[0] = {"delta": {"content": "K"}}
                                content = delta.get("content", "")  # content = "K"
                                if content:
                                    yield content # Yield the content token by token
                        except json.JSONDecodeError:
                            continue # Ignore JSON parsing errors and continue streaming