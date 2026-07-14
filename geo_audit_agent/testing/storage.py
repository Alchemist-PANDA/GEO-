import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

def write_result_jsonl(file_path: str, result: dict[str, Any]):
    """Appends a single test result JSON object as a line to the specified file."""
    # Ensure directory exists
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result) + "\n")
        f.flush()

def load_completed_test_ids(file_path: str) -> set[str]:
    """Reads existing JSONL file and collects all test_ids that succeeded."""
    completed: set[str] = set()
    if not os.path.exists(file_path):
        return completed

    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # We only resume if the test status was 'success'
                    if data.get("status") == "success" and "test_id" in data:
                        completed.add(data["test_id"])
                except Exception:
                    # Skip malformed lines
                    continue
        logger.info(f"Resuming: found {len(completed)} completed test cases in {os.path.basename(file_path)}.")
    except Exception as e:
        logger.warning(f"Error reading existing results file for resume: {e}. Starting fresh.")

    return completed
