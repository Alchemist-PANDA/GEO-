"""Fail CI when tracked files contain common credential signatures."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

PATTERNS = {
    "Google API key": re.compile("AI" + r"za[0-9A-Za-z_-]{30,}"),
    "OpenAI API key": re.compile("sk" + r"-(?:proj-|svcacct-)?[A-Za-z0-9]{20,}"),
    "Anthropic API key": re.compile("sk" + r"-ant-api03-[A-Za-z0-9_-]{20,}"),
    "private key": re.compile("BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY"),
}
ALLOWLIST = {".env.example", "scripts/check_secrets.py", "tests/test_guardrail_handlers.py"}
PLACEHOLDER_MARKERS = ("test", "your", "example", "placeholder", "fake", "dummy", "xxxx")


def main() -> int:
    tracked = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    findings = []
    for name in tracked:
        if not name or name in ALLOWLIST:
            continue
        path = Path(name)
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            match = pattern.search(content)
            if match and not any(marker in match.group(0).lower() for marker in PLACEHOLDER_MARKERS):
                findings.append(f"{name}: possible {label}")
    if findings:
        print("\n".join(findings))
        return 1
    print("Tracked-tree credential scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
