from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class Severity(str, Enum):
    LOW = "low"; MEDIUM = "medium"; HIGH = "high"; CRITICAL = "critical"

@dataclass
class Violation:
    guardrail_type: str
    rule: str
    severity: Severity
    message: str
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class GuardrailDecision:
    allowed: bool
    violations: list[Violation] = field(default_factory=list)
    @property
    def blocked(self) -> bool:
        return not self.allowed
