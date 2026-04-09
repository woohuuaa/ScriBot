import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.cache import TTLCache, build_cache_key, cache_service, normalize_cache_text


class TTLCacheTests(unittest.TestCase):
    def test_set_and_get_value(self):
        cache = TTLCache(max_entries=2)
        cache.set("a", {"value": 1}, ttl_seconds=10)
        self.assertEqual(cache.get("a"), {"value": 1})

    def test_expired_entry_misses(self):
        cache = TTLCache(max_entries=2)
        cache.set("a", "hello", ttl_seconds=1)
        time.sleep(1.1)
        self.assertIsNone(cache.get("a"))

    def test_lru_eviction_removes_oldest_entry(self):
        cache = TTLCache(max_entries=2)
        cache.set("a", 1, ttl_seconds=10)
        cache.set("b", 2, ttl_seconds=10)
        self.assertEqual(cache.get("a"), 1)
        cache.set("c", 3, ttl_seconds=10)

        self.assertIsNone(cache.get("b"))
        self.assertEqual(cache.get("a"), 1)
        self.assertEqual(cache.get("c"), 3)


class CacheServiceTests(unittest.TestCase):
    def setUp(self):
        cache_service.clear_all_caches()

    def test_docs_generation_bump_clears_caches(self):
        generation_before = cache_service.get_docs_generation()
        cache_service.rag_cache.set("rag", "value", ttl_seconds=10)
        cache_service.chat_response_cache.set("chat", "answer", ttl_seconds=10)

        generation_after = cache_service.bump_docs_generation()

        self.assertEqual(generation_after, generation_before + 1)
        self.assertIsNone(cache_service.rag_cache.get("rag"))
        self.assertIsNone(cache_service.chat_response_cache.get("chat"))

    def test_cache_key_changes_with_generation(self):
        normalized = normalize_cache_text("What is   KDAI?  ")
        key_before = build_cache_key("chat", normalized, "groq", "model-a", cache_service.get_docs_generation())
        next_generation = cache_service.bump_docs_generation()
        key_after = build_cache_key("chat", normalized, "groq", "model-a", next_generation)

        self.assertNotEqual(key_before, key_after)

    def test_mark_docs_changed_records_reason(self):
        cache_service.mark_docs_changed("upload_reference:file.pdf")
        stats = cache_service.get_stats()

        self.assertEqual(stats["last_invalidation_reason"], "upload_reference:file.pdf")
        self.assertIsNotNone(stats["last_invalidation_at"])


if __name__ == "__main__":
    unittest.main()
