import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from main import app


class FakeProvider:
    model = "fake-model"

    def get_name(self) -> str:
        return "groq"

    async def generate_stream(self, prompt: str, system_prompt: str | None = None):
        yield "Hello"
        yield " world"


class ChatSourcesTests(unittest.TestCase):
    def test_chat_stream_emits_sources_metadata_event(self):
        client = TestClient(app)
        fake_rag_result = {
            "prompt": "ignored",
            "sources": [{"source": "architecture.mdx", "title": "Architecture"}],
        }

        with patch("main.get_llm_provider", return_value=FakeProvider()), patch(
            "main.rag_service.query",
            new=AsyncMock(return_value=fake_rag_result),
        ):
            response = client.post(
                "/api/chat",
                json={"question": "What is KDAI?", "provider": "groq"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("data: Hello", response.text)
        self.assertIn('[META] {"type": "sources", "sources": [{"source": "architecture.mdx", "title": "Architecture"}]}', response.text)
        self.assertIn("data: [DONE]", response.text)


if __name__ == "__main__":
    unittest.main()
