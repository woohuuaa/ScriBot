import re


TRADITIONAL_MARKERS = set("體繁請麼這個為與還說網應檔點問題舉例變時後開關處理讓會嗎實際網站")
SIMPLIFIED_MARKERS = set("体繁请么这个为与还说网应档点问题举例变时后开关处理让会吗实际网站")

EXPLICIT_LANGUAGE_PATTERNS = [
    (r"(?:please|pls)\s+(?:answer|respond|reply)\s+in\s+english", "English"),
    (r"(?:please|pls)\s+(?:answer|respond|reply)\s+in\s+dutch", "Dutch"),
    (r"請\s*用\s*英文\s*回答", "English"),
    (r"請\s*用\s*荷蘭文\s*回答", "Dutch"),
    (r"請\s*用\s*繁體中文\s*回答", "Traditional Chinese"),
    (r"請\s*用\s*简体中文\s*回答", "Simplified Chinese"),
    (r"请\s*用\s*英文\s*回答", "English"),
    (r"请\s*用\s*荷兰文\s*回答", "Dutch"),
    (r"请\s*用\s*繁體中文\s*回答", "Traditional Chinese"),
    (r"请\s*用\s*简体中文\s*回答", "Simplified Chinese"),
]

DUTCH_MARKERS = {
    "de", "het", "een", "wat", "hoe", "vergelijk", "vereisten", "functionele", "niet-functionele",
}


def detect_explicit_language_request(question: str) -> str | None:
    lowered = question.lower()
    for pattern, language in EXPLICIT_LANGUAGE_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return language
    return None


def detect_chinese_variant(question: str) -> str | None:
    traditional_score = sum(1 for char in question if char in TRADITIONAL_MARKERS)
    simplified_score = sum(1 for char in question if char in SIMPLIFIED_MARKERS)

    if traditional_score > simplified_score:
        return "Traditional Chinese"

    if simplified_score > traditional_score:
        return "Simplified Chinese"

    return None


def detect_primary_non_chinese_language(question: str) -> str:
    tokens = re.findall(r"[a-zA-Z]+", question.lower())
    if any(token in DUTCH_MARKERS for token in tokens):
        return "Dutch"
    return "English"


def detect_response_language(question: str) -> str:
    explicit_language = detect_explicit_language_request(question)
    if explicit_language:
        return explicit_language

    chinese_chars = re.findall(r"[\u4e00-\u9fff]", question)
    latin_tokens = re.findall(r"[a-zA-Z]+", question)
    chinese_count = len(chinese_chars)
    latin_count = len(latin_tokens)

    # Avoid switching to Chinese for mostly-English prompts that merely quote a Chinese term.
    chinese_is_primary = chinese_count >= 6 or (chinese_count >= 3 and chinese_count > latin_count)
    if chinese_is_primary:
        return detect_chinese_variant(question) or detect_primary_non_chinese_language(question)

    if chinese_count and latin_count == 0:
        return detect_chinese_variant(question) or "Traditional Chinese"

    return detect_primary_non_chinese_language(question)


def build_language_instruction(question: str) -> str:
    explicit_language = detect_explicit_language_request(question)
    response_language = detect_response_language(question)

    if explicit_language:
        return f"The user explicitly requested {explicit_language}. Answer in {explicit_language} only."

    return (
        f"The user's primary language is {response_language}. Answer in {response_language} only. "
        "Do not switch languages because the documentation or tool output uses a different language."
    )
