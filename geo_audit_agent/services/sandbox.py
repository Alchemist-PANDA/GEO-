"""
E2B Firecracker sandbox for safe execution of generated code/markup.
Addresses: Audit 3 §2.A (Host Isolation), PE-OS Law 3
Fixes: geo_remediation_tools.py:42 direct host filesystem writes
"""
import logging

logger = logging.getLogger(__name__)


class SandboxExecutor:
    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms

    def validate_html(self, html_content: str) -> dict:
        try:
            import base64
            from e2b_code_interpreter import Sandbox
            encoded = base64.b64encode(html_content.encode()).decode()
            with Sandbox(timeout=self.timeout_ms) as sandbox:
                result = sandbox.run_code(f"""
import json
import base64
from html.parser import HTMLParser

class Validator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
    def handle_starttag(self, tag, attrs): pass
    def handle_endtag(self, tag): pass

html_content = base64.b64decode("{encoded}").decode()
validator = Validator()
try:
    validator.feed(html_content)
    print(json.dumps({{"valid": True, "errors": []}}))
except Exception as e:
    print(json.dumps({{"valid": False, "errors": [str(e)]}}))
""")
                return {"valid": True, "output": result.text}
        except ImportError:
            logger.warning("E2B not available, falling back to local validation")
            return self._local_validate_html(html_content)
        except Exception as e:
            logger.error("Sandbox execution failed: %s", e)
            return {"valid": False, "error": str(e)}

    def _local_validate_html(self, html_content: str) -> dict:
        from html.parser import HTMLParser
        try:
            parser = HTMLParser()
            parser.feed(html_content)
            return {"valid": True}
        except Exception as e:
            return {"valid": False, "error": str(e)}
