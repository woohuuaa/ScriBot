import json
import re

from services.agent.prompts import build_agent_prompt
from services.agent.tools.base import Tool


# ─────────────────────────────────────────────────────────────
# ReAct Agent
# ─────────────────────────────────────────────────────────────


class Agent:
    """
    ReAct Agent for KDAI documentation
    """

    def __init__(self, llm_provider, tools: list[Tool], max_steps: int = 10):
        self.llm = llm_provider
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        self.tool_dicts = [tool.to_dict() for tool in tools]

    async def run(self, user_input: str) -> dict:
        """
        Run the agent loop

        """
        self.system_prompt = build_agent_prompt(self.tool_dicts, user_input)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]

        steps = []
        collected_sources = []

        for step_num in range(self.max_steps):
            response = await self._get_llm_response(messages)
            parsed = self._parse_response(response)

            step_data = {
                "step": step_num + 1,
                "thought": parsed.get("thought", ""),
                "action": parsed.get("action"),
                "action_input": parsed.get("action_input"),
                "final_answer": parsed.get("final_answer"),
            }
            steps.append(step_data)
            
            if parsed.get("final_answer"):
                fallback_sources = self._extract_sources(parsed["final_answer"])
                return {
                    "answer": parsed["final_answer"],
                    "steps": steps,
                    "sources": collected_sources or fallback_sources,
                }

            if parsed.get("action"):
                observation = await self._execute_tool(
                    parsed["action"],
                    parsed.get("action_input", {}),
                )
                collected_sources = self._merge_sources(collected_sources, self._get_tool_sources(parsed["action"]))

                messages.append({"role": "assistant", "content": response}) 
                messages.append({"role": "user", "content": f"Observation: {observation}"}) 
                steps[-1]["observation"] = observation 
            else:   
                messages.append({"role": "assistant", "content": response}) 
                messages.append(
                    {
                        "role": "user",
                        "content": "Please follow exactly Format A or Format B.",
                    }
                )

        return {
            "answer": "I could not complete the task within the allowed steps.",
            "steps": steps,
            "sources": collected_sources,
        }

    async def _get_llm_response(self, messages: list[dict]) -> str:
        """
        Get a non-streaming response using generate_stream(prompt)
        """
        prompt = self._build_conversation_prompt(messages) 

        response = ""
        async for chunk in self.llm.generate_stream(prompt, system_prompt=self.system_prompt):
            response += chunk

        return response.strip()


    def _build_conversation_prompt(self, messages: list[dict]) -> str: 
        """
        Flatten messages into a single prompt string
        """
        parts = []
        for message in messages:
            if message["role"] == "system":
                continue
            parts.append(f"{message['role'].upper()}:\n{message['content']}") 

        parts.append("ASSISTANT:")
        return "\n\n".join(parts)

    def _parse_response(self, response: str) -> dict:
        """
        Parse Thought / Action / Action Input / Final Answer
        """
        result = {}

        thought_match = re.search(
            r"Thought:\s*(.+?)(?=Action:|Final Answer:|$)",
            response,
            re.DOTALL,
        )
        if thought_match:
            result["thought"] = thought_match.group(1).strip() 

        final_match = re.search(r"Final Answer:\s*(.+)", response, re.DOTALL) 
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result

        action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)", response)
        if action_match:
            result["action"] = action_match.group(1).strip()

        input_match = re.search(r"Action Input:\s*(\{.*\})", response, re.DOTALL)
        if input_match:
            raw_input = input_match.group(1).strip()
            try:
                result["action_input"] = json.loads(raw_input)
            except json.JSONDecodeError:
                result["action_input"] = {}

        return result

    async def _execute_tool(self, tool_name: str, params: dict) -> str:
        """
        Execute a tool and return observation
        """
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Error: Unknown tool '{tool_name}'. Available tools: {list(self.tools.keys())}"

        try:
            return await tool.execute(**params)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def _get_tool_sources(self, tool_name: str) -> list[dict]:
        tool = self.tools.get(tool_name)
        sources = getattr(tool, "last_sources", None)
        if isinstance(sources, list):
            return sources
        return []

    def _merge_sources(self, existing: list[dict], incoming: list[dict]) -> list[dict]:
        merged = list(existing)
        seen = {(item.get("source"), item.get("title")) for item in existing}
        for item in incoming:
            key = (item.get("source"), item.get("title"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged

    def _extract_sources(self, answer: str) -> list[dict]:
        """
        Extract simple source citations from the final answer
        """
        sources = []
        sources_match = re.search(r"Sources?:\s*\n((?:[-•]\s*.+\n?)*)", answer)
        if not sources_match:
            return sources

        for line in sources_match.group(1).strip().splitlines():
            match = re.match(r"[-•]\s*(.+)", line.strip())
            if match:
                sources.append({"source": match.group(1)})

        return sources
