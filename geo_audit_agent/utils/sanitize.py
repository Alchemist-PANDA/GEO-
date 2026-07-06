"""Input sanitization for LLM prompts and HTML output."""
import html
import re

_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|(?:im_start|im_end|system)\|>", re.IGNORECASE),
]

MAX_BRAND_NAME_LEN = 255
MAX_CATEGORY_LEN = 100
MAX_CITY_LEN = 100


def sanitize_for_prompt(value: str, max_length: int = 255) -> str:
    value = value.strip()[:max_length]
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
    return value


def sanitize_brand_name(name: str) -> str:
    return sanitize_for_prompt(name, MAX_BRAND_NAME_LEN)


def sanitize_category(category: str) -> str:
    return sanitize_for_prompt(category, MAX_CATEGORY_LEN)


def sanitize_city(city: str) -> str:
    return sanitize_for_prompt(city, MAX_CITY_LEN)


def escape_html(value: str) -> str:
    return html.escape(value, quote=True)


def check_prompt_injection(text: str) -> bool:
    return any(p.search(text) for p in _PROMPT_INJECTION_PATTERNS)
