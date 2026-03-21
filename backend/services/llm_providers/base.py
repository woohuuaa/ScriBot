# backend/services/llm_providers/base.py
# Base class for LLM providers 

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
    
    所有 LLM Provider 必須實作：
    1. generate_stream() - 串流生成回應
    2. get_name() - 取得 Provider 名稱
    
    Why abstract?
    → 確保所有 Provider 有一致的介面
    → 避免某個 Provider 漏掉實作某個方法
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
            str: Response tokens, one by one / 回應的 token, 逐字產生
            
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