import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.agent.agent import Agent
from services.agent.tools.base import Tool
from services.agent.prompts import build_agent_prompt
from services.language import build_language_instruction, detect_response_language


class DummyTool(Tool):
    @property
    def name(self) -> str:
        return "dummy_tool"

    @property
    def description(self) -> str:
        return "Dummy tool for testing"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> str:
        return "ok"


class FakeLLM:
    def __init__(self):
        self.calls = []

    async def generate_stream(self, prompt: str, system_prompt: str | None = None):
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        yield "Thought: enough info\nFinal Answer: test"


class LanguageDetectionTests(unittest.TestCase):
    def test_detects_english_question(self):
        self.assertEqual(detect_response_language("What is KDAI?"), "English")

    def test_detects_traditional_chinese_question(self):
        self.assertEqual(detect_response_language("請介紹 KDAI 是什麼"), "Traditional Chinese")

    def test_detects_simplified_chinese_question(self):
        self.assertEqual(detect_response_language("请介绍 KDAI 是什么"), "Simplified Chinese")

    def test_detects_dutch_question(self):
        self.assertEqual(detect_response_language("Wat is KDAI?"), "Dutch")

    def test_keeps_english_for_mixed_prompt_with_short_chinese_term(self):
        self.assertEqual(detect_response_language('What does "請求" mean in this workflow?'), "English")

    def test_explicit_language_request_overrides_question_language(self):
        self.assertEqual(detect_response_language("請介紹 KDAI, please answer in English."), "English")

    def test_language_instruction_mentions_primary_language(self):
        instruction = build_language_instruction("Explain Docker and 「容器」 in KDAI.")
        self.assertIn("The user's primary language is English.", instruction)


class AgentPromptTests(unittest.TestCase):
    def test_build_agent_prompt_includes_language_rule_for_user_input(self):
        prompt = build_agent_prompt([], "What is KDAI?")
        self.assertIn("The user's primary language is English.", prompt)
        self.assertIn("Use the user's latest message, not tool output language", prompt)

    def test_agent_passes_real_system_prompt_to_provider(self):
        llm = FakeLLM()
        agent = Agent(llm_provider=llm, tools=[DummyTool()])

        result = asyncio.run(agent.run("What is KDAI?"))

        self.assertEqual(result["answer"], "test")
        self.assertEqual(len(llm.calls), 1)
        self.assertIn("The user's primary language is English.", llm.calls[0]["system_prompt"])
        self.assertNotIn("SYSTEM:\n", llm.calls[0]["prompt"])


if __name__ == "__main__":
    unittest.main()
