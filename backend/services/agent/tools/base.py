from abc import ABC, abstractmethod

# ─────────────────────────────────────────────────────────────
# Tool Base Class
# ─────────────────────────────────────────────────────────────
#
# Why use an abstract base class?
#   - Standardize the interface for all tools
#   - Let the Agent discover and call tools dynamically
#   - Make new tools easy to add
#
# Every tool must implement:
#   - name: tool name used by the Agent
#   - description: helps the Agent choose when to use it
#   - parameters: JSON Schema for tool inputs
#   - execute(): actual tool logic
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
