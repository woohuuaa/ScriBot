import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from config import settings
from main import app
from services.cache import cache_service


class CacheAdminEndpointTests(unittest.TestCase):
    def setUp(self):
        self.original_token = settings.admin_token
        settings.admin_token = "test-token"
        cache_service.clear_all_caches()
        self.client = TestClient(app)

    def tearDown(self):
        settings.admin_token = self.original_token

    def test_cache_stats_requires_admin_token(self):
        response = self.client.get("/api/admin/cache/stats")
        self.assertEqual(response.status_code, 403)

    def test_cache_stats_returns_generation_and_namespaces(self):
        cache_service.rag_cache.set("rag", "value", ttl_seconds=10)
        cache_service.mark_docs_changed("test-upload")

        response = self.client.get(
            "/api/admin/cache/stats",
            headers={"x-admin-token": "test-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["last_invalidation_reason"], "test-upload")
        self.assertIn("rag", payload)
        self.assertIn("chat_response", payload)
        self.assertIn("agent_response", payload)

    def test_cache_clear_empties_namespaces_without_changing_generation(self):
        cache_service.chat_response_cache.set("chat", "answer", ttl_seconds=10)
        generation = cache_service.mark_docs_changed("seed-generation")
        cache_service.chat_response_cache.set("chat", "answer", ttl_seconds=10)

        response = self.client.post(
            "/api/admin/cache/clear",
            headers={"x-admin-token": "test-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "cleared")
        self.assertEqual(payload["docs_generation"], generation)
        self.assertIsNone(cache_service.chat_response_cache.get("chat"))


if __name__ == "__main__":
    unittest.main()
