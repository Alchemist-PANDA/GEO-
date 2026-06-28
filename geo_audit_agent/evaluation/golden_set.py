"""Versioned golden traces — the regression suite for self-improvement."""
import json
import pathlib
_PATH = pathlib.Path("data/golden_set.jsonl")

def load() -> list[dict]:
    if not _PATH.exists():
        return []
    return [json.loads(l) for l in _PATH.read_text().splitlines() if l.strip()]

def add(case: dict):
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    with _PATH.open("a") as f:
        f.write(json.dumps(case) + "\n")
