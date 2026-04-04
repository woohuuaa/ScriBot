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
        prompt: str
    ) -> AsyncGenerator[str, None]:
        """
        Generate response with streaming
        
        Args:
            prompt: The input prompt
            
        Yields:
            str: Response tokens, one by one
            
        Why AsyncGenerator?
        → LLM 回應是「慢慢」產生的
        → 一次吐一個 token，而不是等全部完成
        → 實現 ChatGPT 那種「逐字顯示」的效果
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get provider name
        
        Returns:
            str: Provider name (e.g., "ollama", "groq") / Provider 名稱
            
        用處：
        → Logging / 記錄用哪個 Provider
        → Monitoring / 監控時區分 Provider
        → Error messages / 錯誤訊息
        """
        pass
    
    def get_cost_per_token(self) -> float:
        """
        Get cost per token / 取得每個 token 的成本
        
        Returns:
            float: Cost per 1K tokens / 每 1000 個 token 的成本
            
        預設回傳 0（用於 Ollama 本地）
        子類別可以 override / 覆寫
        """
        return 0.0  # Default: free (Ollama local)