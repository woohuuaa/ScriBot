import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock

from config import settings


@dataclass
class CacheEntry:
    value: object
    expires_at: float


class TTLCache:
    def __init__(self, max_entries: int):
        self.max_entries = max(1, max_entries)
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "evictions": 0,
        }

    def get(self, key: str):
        now = time.time()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self.stats["misses"] += 1
                return None

            if entry.expires_at <= now:
                self._entries.pop(key, None)
                self.stats["misses"] += 1
                return None

            self._entries.move_to_end(key)
            self.stats["hits"] += 1
            return entry.value

    def set(self, key: str, value: object, ttl_seconds: int):
        expires_at = time.time() + max(1, ttl_seconds)
        with self._lock:
            self._entries[key] = CacheEntry(value=value, expires_at=expires_at)
            self._entries.move_to_end(key)
            self.stats["writes"] += 1

            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
                self.stats["evictions"] += 1

    def clear(self):
        with self._lock:
            self._entries.clear()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "size": len(self._entries),
                **self.stats,
            }


def normalize_cache_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def build_cache_key(*parts: object) -> str:
    raw = json.dumps(parts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CacheService:
    def __init__(self):
        self.rag_cache = TTLCache(settings.rag_cache_max_entries)
        self.chat_response_cache = TTLCache(settings.chat_response_cache_max_entries)
        self.agent_response_cache = TTLCache(settings.agent_response_cache_max_entries)
        self._docs_generation = 0
        self._last_invalidation_reason = None
        self._last_invalidation_at = None
        self._lock = Lock()

    def get_docs_generation(self) -> int:
        with self._lock:
            return self._docs_generation

    def bump_docs_generation(self, reason: str | None = None) -> int:
        with self._lock:
            self._docs_generation += 1
            generation = self._docs_generation
            self._last_invalidation_reason = reason
            self._last_invalidation_at = time.time()

        self.clear_all_caches()
        return generation

    def mark_docs_changed(self, reason: str) -> int:
        return self.bump_docs_generation(reason=reason)

    def clear_all_caches(self):
        self.rag_cache.clear()
        self.chat_response_cache.clear()
        self.agent_response_cache.clear()

    def get_stats(self) -> dict:
        return {
            "docs_generation": self.get_docs_generation(),
            "last_invalidation_reason": self._last_invalidation_reason,
            "last_invalidation_at": self._last_invalidation_at,
            "rag": self.rag_cache.snapshot(),
            "chat_response": self.chat_response_cache.snapshot(),
            "agent_response": self.agent_response_cache.snapshot(),
        }


cache_service = CacheService()
