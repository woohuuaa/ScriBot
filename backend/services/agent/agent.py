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

        tool_dicts = [tool.to_dict() for tool in tools]
        self.system_prompt = build_agent_prompt(tool_dicts) 

    async def run(self, user_input: str) -> dict:
        """
        Run the agent loop

        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]

        steps = []

        for step_num in range(self.max_steps):
            response = await self._get_llm_response(messages) # from selected llm: generate_stream(prompt)
            parsed = self._parse_response(response) # Parse text to Thought / Action / Action Input / Final Answer

            step_data = {
                "step": step_num + 1,
                "thought": parsed.get("thought", ""),
                "action": parsed.get("action"),
                "action_input": parsed.get("action_input"),
                "final_answer": parsed.get("final_answer"),
            }
            steps.append(step_data)
            
            # If there's a final answer, return it along with the steps and extracted sources
            if parsed.get("final_answer"): 
                return {
                    "answer": parsed["final_answer"],
                    "steps": steps,
                    "sources": self._extract_sources(parsed["final_answer"]),
                }

            # If there's an action, execute the tool and get the observation, then add it to the conversation history for the next step.
            if parsed.get("action"):
                observation = await self._execute_tool(
                    parsed["action"], # Tool name to execute
                    parsed.get("action_input", {}), # Parameters for the tool, defaulting to an empty dict if not provided
                )

                # Add the LLM's response and the tool observation to the conversation history for the next step.
                # This allows the LLM to see the result of its action in the next turn, enabling it to reason 
                # based on the observation and decide on the next action or final answer.
                messages.append({"role": "assistant", "content": response}) 
                messages.append({"role": "user", "content": f"Observation: {observation}"}) 
                steps[-1]["observation"] = observation 
            else:   
                messages.append({"role": "assistant", "content": response}) 
                messages.append( 
                        "role": "user",
                        "content": "Please follow exactly Format A or Format B.",
                    }
                )

        return {
            "answer": "I could not complete the task within the allowed steps.",
            "steps": steps,
            "sources": [],
        }

    async def _get_llm_response(self, messages: list[dict]) -> str:
        """
        Get a non-streaming response using generate_stream(prompt)
        """
        prompt = self._build_conversation_prompt(messages) 

        response = ""
        async for chunk in self.llm.generate_stream(prompt): # Stream the LLM response and concatenate it into a single string
            response += chunk

        return response.strip()


    def _build_conversation_prompt(self, messages: list[dict]) -> str: 
        """
        Flatten messages into a single prompt string
        """
        parts = []
        for message in messages:
            # For each message in the conversation history, add it to the prompt with the role (USER or ASSISTANT) and the content. 
            # This creates a single string that represents the entire conversation history, which can be fed into the LLM as context 
            # for generating the next response.
            parts.append(f"{message['role'].upper()}:\n{message['content']}") 

        parts.append("ASSISTANT:")
        return "\n\n".join(parts)

    def _parse_response(self, response: str) -> dict:
        """
        Parse Thought / Action / Action Input / Final Answer
        """
        result = {}

        thought_match = re.search(
            # Non-greedy match for Thought until Action: or Final Answer: or end of string, allowing Thought to span multiple lines if needed
            r"Thought:\s*(.+?)(?=Action:|Final Answer:|$)",
            response,
            re.DOTALL, # Allow Thought to span multiple lines if needed
        )
        # If a Thought is found, extract it and strip leading/trailing whitespace. 
        # This captures the LLM's internal reasoning or thought process before it decides on an action or final answer.
        if thought_match:
            result["thought"] = thought_match.group(1).strip() 

        # Match Final Answer and capture everything after it (including newlines) as the final answer content. 
        # This assumes that if there's a Final Answer, it will be the last part of the response, and can include multiple lines of text.
        final_match = re.search(r"Final Answer:\s*(.+)", response, re.DOTALL) 
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result

        # Match Action and capture the action name (assuming it's a single word or identifier).
        # This captures the tool that the LLM has decided to use based on its reasoning.
        action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)", response)
        if action_match:
            result["action"] = action_match.group(1).strip()

        # Match Action Input and capture everything after it (including newlines) as the action input content.
        # This assumes that the action input will be provided in JSON format, and can span multiple lines. 
        # The regex captures everything after "Action Input:" as the raw input string.
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
            # Execute the tool's asynchronous execute method with the provided parameters and return the observation.
            # This assumes that the tool's execute method is designed to take keyword arguments corresponding to the 
            # parameters specified in the action input, and that it returns a string observation that can be fed back 
            # into the conversation history for the LLM to use in subsequent reasoning steps.
            return await tool.execute(**params)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def _extract_sources(self, answer: str) -> list[dict]:
        """
        Extract simple source citations from the final answer
        """
        sources = []
        # Look for a "Sources:" section in the final answer and extract each source listed under it, 
        # assuming sources are listed as bullet points (e.g., "- Source 1").
        sources_match = re.search(r"Sources?:\s*\n((?:[-•]\s*.+\n?)*)", answer)
        if not sources_match:
            return sources

        # For each line in the Sources section, match lines that start with a bullet point and extract the source text, 
        # adding it to the list of sources.
        for line in sources_match.group(1).strip().splitlines():
            match = re.match(r"[-•]\s*(.+)", line.strip())
            if match:
                sources.append({"source": match.group(1)})

        return sources
