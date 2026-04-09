import os
import sys
import time
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.cache import CacheService, TTLCache, build_cache_key, cache_service, normalize_cache_text


class FakeRedisClient:
    def __init__(self):
        self.store = {}
        self.hashes = {}
        self.expiry = {}

    def ping(self):
        return True

    def _expired(self, key: str) -> bool:
        expires_at = self.expiry.get(key)
        return expires_at is not None and expires_at <= time.time()

    def get(self, key: str):
        if self._expired(key):
            self.store.pop(key, None)
            self.expiry.pop(key, None)
            return None
        return self.store.get(key)

    def set(self, key: str, value, ex: int | None = None):
        self.store[key] = str(value)
        if ex is not None:
            self.expiry[key] = time.time() + ex
        else:
            self.expiry.pop(key, None)
        return True

    def incr(self, key: str):
        current = int(self.get(key) or 0) + 1
        self.set(key, current)
        return current

    def hset(self, key: str, mapping: dict):
        current = self.hashes.setdefault(key, {})
        for field, value in mapping.items():
            current[field] = str(value)
        return len(mapping)

    def hgetall(self, key: str):
        return dict(self.hashes.get(key, {}))

    def scan(self, cursor: int = 0, match: str | None = None, count: int = 200):
        prefix = (match or "").rstrip("*")
        keys = [key for key in self.store if key.startswith(prefix)]
        return 0, keys[:count]

    def delete(self, *keys):
        deleted = 0
        for key in keys:
            if key in self.store:
                deleted += 1
                self.store.pop(key, None)
                self.expiry.pop(key, None)
        return deleted


class FailingRedisClientFactory:
    def __call__(self, redis_url: str):
        raise RuntimeError(f"cannot connect to {redis_url}")


def build_test_settings(**overrides):
    defaults = {
        "cache_backend": "memory",
        "redis_url": "redis://fake",
        "redis_prefix": "scribot-test",
        "redis_strict": False,
        "redis_connect_timeout_seconds": 0.1,
        "redis_socket_timeout_seconds": 0.1,
        "rag_cache_max_entries": 2,
        "chat_response_cache_max_entries": 2,
        "agent_response_cache_max_entries": 2,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


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

    def test_memory_stats_include_active_backend(self):
        stats = cache_service.get_stats()
        self.assertEqual(stats["active_backend"], "memory")


class RedisCacheServiceTests(unittest.TestCase):
    def test_redis_backend_reads_and_writes_values(self):
        fake_redis = FakeRedisClient()
        service = CacheService(
            app_settings=build_test_settings(cache_backend="redis", redis_strict=True),
            redis_client_factory=lambda redis_url: fake_redis,
        )

        service.chat_response_cache.set("chat-key", {"answer": "hello"}, ttl_seconds=10)

        self.assertEqual(service.active_backend, "redis")
        self.assertEqual(service.chat_response_cache.get("chat-key"), {"answer": "hello"})
        stats = service.get_stats()
        self.assertEqual(stats["active_backend"], "redis")
        self.assertEqual(stats["chat_response"]["writes"], 1)
        self.assertEqual(stats["chat_response"]["hits"], 1)

    def test_redis_backend_respects_ttl(self):
        fake_redis = FakeRedisClient()
        service = CacheService(
            app_settings=build_test_settings(cache_backend="redis", redis_strict=True),
            redis_client_factory=lambda redis_url: fake_redis,
        )

        service.rag_cache.set("rag-key", {"context": "value"}, ttl_seconds=1)
        time.sleep(1.1)

        self.assertIsNone(service.rag_cache.get("rag-key"))
        self.assertEqual(service.get_stats()["rag"]["misses"], 1)

    def test_redis_generation_and_metadata_are_global(self):
        fake_redis = FakeRedisClient()
        service = CacheService(
            app_settings=build_test_settings(cache_backend="redis", redis_strict=True),
            redis_client_factory=lambda redis_url: fake_redis,
        )

        generation = service.mark_docs_changed("index_docs")
        stats = service.get_stats()

        self.assertEqual(generation, 1)
        self.assertEqual(stats["docs_generation"], 1)
        self.assertEqual(stats["last_invalidation_reason"], "index_docs")
        self.assertIsNotNone(stats["last_invalidation_at"])

    def test_redis_clear_removes_namespace_keys(self):
        fake_redis = FakeRedisClient()
        service = CacheService(
            app_settings=build_test_settings(cache_backend="redis", redis_strict=True),
            redis_client_factory=lambda redis_url: fake_redis,
        )

        service.rag_cache.set("a", {"value": 1}, ttl_seconds=10)
        service.chat_response_cache.set("b", {"value": 2}, ttl_seconds=10)
        service.clear_all_caches()

        self.assertIsNone(service.rag_cache.get("a"))
        self.assertIsNone(service.chat_response_cache.get("b"))

    def test_non_strict_redis_falls_back_to_memory(self):
        service = CacheService(
            app_settings=build_test_settings(cache_backend="redis", redis_strict=False),
            redis_client_factory=FailingRedisClientFactory(),
        )

        self.assertEqual(service.active_backend, "memory")

    def test_strict_redis_raises_when_unavailable(self):
        with self.assertRaises(RuntimeError):
            CacheService(
                app_settings=build_test_settings(cache_backend="redis", redis_strict=True),
                redis_client_factory=FailingRedisClientFactory(),
            )


if __name__ == "__main__":
    unittest.main()
