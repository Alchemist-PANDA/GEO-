from pydantic import BaseModel, Field
from typing import Any
import uuid

class AgenticState(BaseModel):
    # identity / tracing
    trace_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    plan_id: str | None = None
    user_id: str | None = None
    # request
    user_message: str = ""
    intent: str = ""
    brand_name: str = ""
    category: str = ""
    city: str = ""
    # context pipeline
    context: dict = Field(default_factory=dict)
    # agent outputs
    gaps: list = Field(default_factory=list)
    competitor_data: dict = Field(default_factory=dict)
    copilot_answer: str = ""
    action_plan: list = Field(default_factory=list)
    action_results: list = Field(default_factory=list)
    # control + accounting
    next_agent: str = ""
    inspector_verdict: dict = Field(default_factory=dict)
    blocked: bool = False
    block_reason: str = ""
    tokens: int = 0
    cost_usd: float = 0.0

    def action_context(self) -> dict:
        return {"brand": self.brand_name, "category": self.category,
                "city": self.city, "gaps": self.gaps, "score": self.context.get("score")}
