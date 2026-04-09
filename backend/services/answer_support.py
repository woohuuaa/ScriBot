from typing import Literal


AnswerSupport = Literal["supported", "uncertain"]


UNCERTAIN_PATTERNS = [
    "i am not sure based on the documentation",
    "i am not sure from the documentation",
    "the documentation does not provide enough information",
    "i could not find relevant information",
    "i could not find enough information",
    "documentation is insufficient",
    "based on the documentation, i am not sure",
    "根據文件我無法確定",
    "根據文件無法確定",
    "根據文件我不確定",
    "找不到相關資料",
    "沒有足夠資訊",
    "文件沒有提供足夠資訊",
]

INSUFFICIENT_OBSERVATION_PATTERNS = [
    "no relevant documentation found",
    "documentation is insufficient",
    "could not find enough information",
    "找不到相關資料",
    "沒有足夠資訊",
]


def is_uncertain_text(text: str) -> bool:
    normalized = text.strip().lower()
    return any(pattern in normalized for pattern in UNCERTAIN_PATTERNS)


def dedupe_sources(sources: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for source in sources:
        key = (source.get("source"), source.get("title"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)
    return deduped


def select_sources_for_support(sources: list[dict], support: AnswerSupport) -> list[dict]:
    deduped = dedupe_sources(sources)
    return deduped[:3] if support == "uncertain" else deduped


def detect_chat_support(answer: str, rag_results: list[dict]) -> AnswerSupport:
    if not rag_results:
        return "uncertain"
    if is_uncertain_text(answer):
        return "uncertain"
    return "supported"


def detect_agent_support(answer: str, collected_sources: list[dict], steps: list[dict]) -> AnswerSupport:
    if collected_sources:
        return "supported"

    for step in steps:
        observation = str(step.get("observation") or "").strip().lower()
        if any(pattern in observation for pattern in INSUFFICIENT_OBSERVATION_PATTERNS):
            return "uncertain"

    if is_uncertain_text(answer):
        return "uncertain"

    return "supported"
