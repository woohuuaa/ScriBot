import httpx
from typing import AsyncGenerator
from .base import BaseLLMProvider
from config import settings
# ─────────────────────────────────────────────────────────────
# OpenAI Provider Class
# ─────────────────────────────────────────────────────────────
class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI cloud LLM provider
        
    API format:
    POST https://api.openai.com/v1/chat/completions
    Headers: Authorization: Bearer <API_KEY>
    """
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.base_url = "https://api.openai.com/v1"
    
    def get_name(self) -> str:
        """
        Get provider name
        """
        return "openai"
    
    def get_cost_per_token(self) -> float:
        """
        Get cost per token
        
        Returns:
            float: Cost per 1K tokens
            gpt-4o-mini = $0.00015 per 1K tokens (input)
        
        Reference: https://openai.com/pricing
        """
        # gpt-4o-mini pricing (approximate)
        # Input: $0.15 / 1M tokens = $0.00015 / 1K tokens
        # Output: $0.60 / 1M tokens = $0.0006 / 1K tokens
        # Average: ~$0.000375 per 1K tokens
        return 0.000375
    
    async def generate_stream(
        self, 
        prompt: str
    ) -> AsyncGenerator[str, None]:
        """
        Generate response with streaming
        
        OpenAI 的 API 格式：
        POST /chat/completions
        Body: {"model": "gpt-4o-mini", "messages": [...], "stream": true}
        
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
                        json_str = line[5:].strip()
                        
                        # Check for [DONE]
                        if json_str == "[DONE]":
                            break
                        
                        import json
                        try:
                            data = json.loads(json_str)
                            # Extract content from OpenAI format
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue