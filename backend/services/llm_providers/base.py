from abc import ABC, abstractmethod
# abc = Abstract Base Classes module
# ABC = Base class for creating abstract classes
# abstractmethod = decorator that marks a method as abstract
from typing import AsyncGenerator
# AsyncGenerator = a generator that yields async values
# For SSE streaming

# ─────────────────────────────────────────────────────────────
# Base LLM Provider Class
# ─────────────────────────────────────────────────────────────
class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers
    """
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate response with streaming
        
        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt override
            
        Yields:
            str: Response tokens, one by one
            
        Why AsyncGenerator?
        - LLM responses are produced gradually.
        - Tokens can be yielded incrementally instead of waiting for the full response.
        - This enables ChatGPT-style streaming output.
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get provider name
        
        Returns:
            str: Provider name (e.g., "ollama", "groq")
            
        Useful for:
        - Logging
        - Monitoring
        - Error messages
        """
        pass
    
    def get_cost_per_token(self) -> float:
        """
        Get cost per token.
        
        Returns:
            float: Cost per 1K tokens
            
        Defaults to 0.0 for local Ollama.
        Subclasses can override this.
        """
        return 0.0  # Default: free (Ollama local)
