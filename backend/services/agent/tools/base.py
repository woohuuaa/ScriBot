from abc import ABC, abstractmethod
from typing import Any

# ─────────────────────────────────────────────────────────────
# Tool Base Class
# 工具基類
# ─────────────────────────────────────────────────────────────
#
# 為什麼用抽象基類?
#   - 統一所有 tool 的接口
#   - Agent 可以動態發現和調用 tools
#   - 容易擴展新的 tools
#
# 每個 Tool 需要實現:
#   - name: 工具名稱 (Agent 用這個名稱調用)
#   - description: 描述 (幫助 Agent 決定何時使用)
#   - parameters: 參數 schema (JSON Schema 格式)
#   - execute(): 實際執行邏輯
# ─────────────────────────────────────────────────────────────


class Tool(ABC):
    """
    Abstract base class for Agent tools
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name for Agent to reference
        
        Example: "search_docs"
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Description of what this tool does and when to use it
        
        Example: "Search KDAI documentation for relevant information"
        """
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        JSON Schema for tool parameters
        
        Example:
        {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        Execute the tool with given parameters
        
        Args:
            **kwargs: Parameters matching the schema
            
        Returns:
            str: Tool execution result (will be shown to Agent)
        """
        pass
    
    def to_dict(self) -> dict:
        """
        Convert tool to dict for LLM prompt
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }