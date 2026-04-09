import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from main import app


class FakeProvider:
    model = "fake-model"

    def __init__(self, chunks=None):
        self.chunks = chunks or ["Hello", " world"]

    def get_name(self) -> str:
        return "groq"

    async def generate_stream(self, prompt: str, system_prompt: str | None = None):
        for chunk in self.chunks:
            yield chunk


class ChatSourcesTests(unittest.TestCase):
    def test_chat_stream_emits_sources_metadata_event(self):
        client = TestClient(app)
        fake_rag_result = {
            "prompt": "ignored",
            "results": [{"source": "architecture.mdx"}],
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
        self.assertIn('[META] {"type": "metadata", "sources": [{"source": "architecture.mdx", "title": "Architecture"}], "support": "supported"}', response.text)
        self.assertIn("data: [DONE]", response.text)

    def test_chat_stream_marks_uncertain_answers_and_limits_sources(self):
        client = TestClient(app)
        fake_rag_result = {
            "prompt": "ignored",
            "results": [],
            "sources": [
                {"source": "a.mdx", "title": "A"},
                {"source": "b.mdx", "title": "B"},
                {"source": "c.mdx", "title": "C"},
                {"source": "d.mdx", "title": "D"},
            ],
        }

        with patch("main.get_llm_provider", return_value=FakeProvider(["I am not sure based on the documentation."])), patch(
            "main.rag_service.query",
            new=AsyncMock(return_value=fake_rag_result),
        ):
            response = client.post(
                "/api/chat",
                json={"question": "Unknown?", "provider": "groq"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn('"support": "uncertain"', response.text)
        self.assertNotIn('"source": "d.mdx"', response.text)


if __name__ == "__main__":
    unittest.main()
