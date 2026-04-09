import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock

import redis

from config import settings


@dataclass
class CacheEntry:
    value: object
    expires_at: float


def normalize_cache_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def build_cache_key(*parts: object) -> str:
    raw = json.dumps(parts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class MemoryNamespaceCache:
    def __init__(self, max_entries: int, stats: dict):
        self.max_entries = max(1, max_entries)
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._stats = stats

    def get(self, key: str):
        now = time.time()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.expires_at <= now:
                self._entries.pop(key, None)
                self._stats["misses"] += 1
                return None

            self._entries.move_to_end(key)
            self._stats["hits"] += 1
            return entry.value

    def set(self, key: str, value: object, ttl_seconds: int):
        expires_at = time.time() + max(1, ttl_seconds)
        with self._lock:
            self._entries[key] = CacheEntry(value=value, expires_at=expires_at)
            self._entries.move_to_end(key)
            self._stats["writes"] += 1

            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
                self._stats["evictions"] += 1

    def clear(self):
        with self._lock:
            self._entries.clear()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "size": len(self._entries),
                **self._stats,
            }
class TTLCache(MemoryNamespaceCache):
    def __init__(self, max_entries: int):
        super().__init__(max_entries=max_entries, stats={"hits": 0, "misses": 0, "writes": 0, "evictions": 0})


class RedisNamespaceCache:
    def __init__(self, client, prefix: str, namespace: str):
        self.client = client
        self.prefix = prefix
        self.namespace = namespace

    def _data_key(self, key: str) -> str:
        return f"{self.prefix}:{self.namespace}:{key}"

    def _stat_key(self, metric: str) -> str:
        return f"{self.prefix}:stats:{self.namespace}:{metric}"

    def get(self, key: str):
        raw = self.client.get(self._data_key(key))
        if raw is None:
            self.client.incr(self._stat_key("misses"))
            return None

        self.client.incr(self._stat_key("hits"))
        return json.loads(raw)

    def set(self, key: str, value: object, ttl_seconds: int):
        self.client.set(self._data_key(key), json.dumps(value, ensure_ascii=False), ex=max(1, ttl_seconds))
        self.client.incr(self._stat_key("writes"))

    def clear(self):
        cursor = 0
        pattern = f"{self.prefix}:{self.namespace}:*"
        while True:
            cursor, keys = self.client.scan(cursor=cursor, match=pattern, count=200)
            if keys:
                self.client.delete(*keys)
            if cursor == 0:
                break

    def snapshot(self) -> dict:
        return {
            "hits": int(self.client.get(self._stat_key("hits")) or 0),
            "misses": int(self.client.get(self._stat_key("misses")) or 0),
            "writes": int(self.client.get(self._stat_key("writes")) or 0),
        }


class CacheService:
    def __init__(self, app_settings=None, redis_client_factory=None):
        self.settings = app_settings or settings
        self.redis_client_factory = redis_client_factory or self._default_redis_client_factory
        self.active_backend = "memory"
        self._last_invalidation_reason = None
        self._last_invalidation_at = None
        self._docs_generation = 0
        self._lock = Lock()
        self._memory_stats = {
            "rag": {"hits": 0, "misses": 0, "writes": 0, "evictions": 0},
            "chat_response": {"hits": 0, "misses": 0, "writes": 0, "evictions": 0},
            "agent_response": {"hits": 0, "misses": 0, "writes": 0, "evictions": 0},
        }
        self._redis = None
        self._initialize_backend()

    def _default_redis_client_factory(self, redis_url: str):
        return redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=self.settings.redis_connect_timeout_seconds,
            socket_timeout=self.settings.redis_socket_timeout_seconds,
        )

    def _initialize_backend(self):
        requested_backend = self.settings.cache_backend.lower()
        if requested_backend == "redis":
            self._initialize_redis_backend()
            return

        self._initialize_memory_backend()

    def _initialize_memory_backend(self):
        self.active_backend = "memory"
        self._redis = None
        self.rag_cache = MemoryNamespaceCache(self.settings.rag_cache_max_entries, self._memory_stats["rag"])
        self.chat_response_cache = MemoryNamespaceCache(
            self.settings.chat_response_cache_max_entries,
            self._memory_stats["chat_response"],
        )
        self.agent_response_cache = MemoryNamespaceCache(
            self.settings.agent_response_cache_max_entries,
            self._memory_stats["agent_response"],
        )

    def _initialize_redis_backend(self):
        try:
            if not self.settings.redis_url:
                raise ValueError("REDIS_URL is required when CACHE_BACKEND=redis")

            client = self.redis_client_factory(self.settings.redis_url)
            client.ping()
            self._redis = client
            self.active_backend = "redis"
            prefix = self.settings.redis_prefix
            self.rag_cache = RedisNamespaceCache(client, prefix, "rag")
            self.chat_response_cache = RedisNamespaceCache(client, prefix, "chat_response")
            self.agent_response_cache = RedisNamespaceCache(client, prefix, "agent_response")
        except Exception:
            if self.settings.redis_strict:
                raise
            self._initialize_memory_backend()

    def _docs_generation_key(self) -> str:
        return f"{self.settings.redis_prefix}:docs_generation"

    def _docs_meta_key(self) -> str:
        return f"{self.settings.redis_prefix}:docs_meta"

    def get_docs_generation(self) -> int:
        if self.active_backend == "redis":
            current = self._redis.get(self._docs_generation_key())
            if current is None:
                self._redis.set(self._docs_generation_key(), 0)
                return 0
            return int(current)

        with self._lock:
            return self._docs_generation

    def bump_docs_generation(self, reason: str | None = None) -> int:
        now = time.time()

        if self.active_backend == "redis":
            generation = int(self._redis.incr(self._docs_generation_key()))
            meta_mapping = {
                "last_invalidation_reason": reason or "",
                "last_invalidation_at": now,
            }
            self._redis.hset(self._docs_meta_key(), mapping=meta_mapping)
            return generation

        with self._lock:
            self._docs_generation += 1
            generation = self._docs_generation
            self._last_invalidation_reason = reason
            self._last_invalidation_at = now

        self.clear_all_caches()
        return generation

    def mark_docs_changed(self, reason: str) -> int:
        return self.bump_docs_generation(reason=reason)

    def clear_all_caches(self):
        self.rag_cache.clear()
        self.chat_response_cache.clear()
        self.agent_response_cache.clear()

    def get_stats(self) -> dict:
        if self.active_backend == "redis":
            metadata = self._redis.hgetall(self._docs_meta_key())
            last_invalidation_reason = metadata.get("last_invalidation_reason") or None
            last_invalidation_at = metadata.get("last_invalidation_at")
            return {
                "active_backend": self.active_backend,
                "docs_generation": self.get_docs_generation(),
                "last_invalidation_reason": last_invalidation_reason,
                "last_invalidation_at": float(last_invalidation_at) if last_invalidation_at else None,
                "rag": self.rag_cache.snapshot(),
                "chat_response": self.chat_response_cache.snapshot(),
                "agent_response": self.agent_response_cache.snapshot(),
            }

        return {
            "active_backend": self.active_backend,
            "docs_generation": self.get_docs_generation(),
            "last_invalidation_reason": self._last_invalidation_reason,
            "last_invalidation_at": self._last_invalidation_at,
            "rag": self.rag_cache.snapshot(),
            "chat_response": self.chat_response_cache.snapshot(),
            "agent_response": self.agent_response_cache.snapshot(),
        }


cache_service = CacheService()
