# ─────────────────────────────────────────────────────────────
# Agent System Prompts
# Agent 系統提示詞
# ─────────────────────────────────────────────────────────────


def build_agent_prompt(tools: list[dict]) -> str:
    """
    Build the agent system prompt with available tools
    
    Args:
        tools: List of tool dicts from Tool.to_dict()
    """
    # Format tools for prompt
    tools_desc = ""
    for tool in tools:
        tools_desc += f"""
### {tool['name']}
{tool['description']}

Parameters:
```json
{tool['parameters']}
```
"""

return f"""You are ScriBot Agent, an AI assistant specialized in KDAI documentation.