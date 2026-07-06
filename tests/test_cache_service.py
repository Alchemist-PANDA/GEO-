"""Tests for the response cache (in-memory fallback path)."""
from geo_audit_agent.services.cache import (
    IN_MEMORY_CACHE,
    get_cache_key,
    get_cached_response,
    set_cached_response,
)


def setup_function(_fn):
    IN_MEMORY_CACHE.clear()


def test_cache_key_deterministic():
    assert get_cache_key("deep", "hello") == get_cache_key("deep", "hello")
    assert get_cache_key("deep", "hello") != get_cache_key("express", "hello")


def test_cache_miss_returns_none():
    assert get_cached_response("deep", "never stored") is None


def test_cache_roundtrip_in_memory():
    set_cached_response("deep", "prompt-1", "cached answer")
    assert get_cached_response("deep", "prompt-1") == "cached answer"


def test_cache_isolated_by_tier():
    set_cached_response("deep", "same prompt", "deep answer")
    assert get_cached_response("express", "same prompt") is None
