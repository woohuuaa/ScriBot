import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from config import settings
from main import agent_rate_limiter, app, chat_rate_limiter
from services.agent.tools.doc_path import resolve_docs_file


class FakeProvider:
    model = "fake-model"

    def get_name(self) -> str:
        return "groq"

    async def generate_stream(self, prompt: str, system_prompt: str | None = None):
        yield "ok"


class FakeAgent:
    tool_names: list[str] = []

    def __init__(self, llm_provider, tools, max_steps=10):
        type(self).tool_names = [tool.name for tool in tools]

    async def run(self, message: str):
        return {
            "answer": "ok",
            "steps": [],
            "sources": [],
            "support": "supported",
        }


class PublicApiGuardrailTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.original_chat_limit = settings.public_chat_requests_per_minute
        self.original_agent_limit = settings.public_agent_requests_per_minute
        self.original_admin_token = settings.admin_token

        settings.public_chat_requests_per_minute = 1
        settings.public_agent_requests_per_minute = 1
        settings.admin_token = "test-token"

        chat_rate_limiter.limit = 1
        agent_rate_limiter.limit = 1
        chat_rate_limiter.clear()
        agent_rate_limiter.clear()

    def tearDown(self):
        settings.public_chat_requests_per_minute = self.original_chat_limit
        settings.public_agent_requests_per_minute = self.original_agent_limit
        settings.admin_token = self.original_admin_token
        chat_rate_limiter.limit = self.original_chat_limit
        agent_rate_limiter.limit = self.original_agent_limit
        chat_rate_limiter.clear()
        agent_rate_limiter.clear()

    def test_chat_rate_limit_blocks_second_request(self):
        fake_rag_result = {
            "prompt": "ignored",
            "results": [{"source": "architecture.mdx"}],
            "sources": [{"source": "architecture.mdx", "title": "Architecture"}],
        }

        with patch("main.get_llm_provider", return_value=FakeProvider()), patch(
            "main.rag_service.query",
            new=AsyncMock(return_value=fake_rag_result),
        ):
            first = self.client.post("/api/chat", json={"question": "What is KDAI?", "provider": "groq"})
            second = self.client.post("/api/chat", json={"question": "What is KDAI?", "provider": "groq"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.headers.get("retry-after"), "60")

    def test_public_agent_uses_read_only_tools(self):
        with patch("main.get_llm_provider", return_value=FakeProvider()), patch("main.Agent", FakeAgent):
            response = self.client.post("/api/agent/run", json={"message": "List docs", "provider": "groq"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FakeAgent.tool_names, ["search_docs", "list_docs", "get_doc_info"])

    def test_admin_agent_enables_document_management_tools(self):
        with patch("main.get_llm_provider", return_value=FakeProvider()), patch("main.Agent", FakeAgent):
            response = self.client.post(
                "/api/agent/run",
                json={"message": "Create a guide", "provider": "groq"},
                headers={"x-admin-token": "test-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            FakeAgent.tool_names,
            ["search_docs", "list_docs", "get_doc_info", "create_doc", "delete_doc"],
        )


class DocPathGuardrailTests(unittest.TestCase):
    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            resolve_docs_file("../escape")

    def test_rejects_absolute_paths(self):
        with self.assertRaises(ValueError):
            resolve_docs_file("/tmp/escape.mdx")


if __name__ == "__main__":
    unittest.main()
