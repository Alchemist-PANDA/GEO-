from typing import Any

from pydantic import BaseModel, Field, model_validator


class AuditState(BaseModel):
    """LangGraph state model for the GEO audit pipeline.

    Maps to the existing agent.py state dict but adds type safety
    and validation boundaries per PE-OS Law 6 (Execution Integrity).
    """
    model_config = {"extra": "allow"}

    # Input fields
    brand_name: str = ""
    brand: str = ""
    business_name: str = ""
    category: str = "business"
    city: str = "Islamabad"
    tier: str = "balanced"
    audit_id: str = ""
    user_id: str = ""
    business_context: Any = None
    template_used: str = ""
    force_mock: bool = False
    use_real: bool = False
    citation_found: bool = False
    mode: str = "simulated"

    # LLM query results
    llm_response: str = ""
    llm_responses: dict[str, str] = Field(default_factory=dict)

    # Citation analysis
    is_cited: bool = False
    confidence_score: float = 0.0
    sentiment: str = "neutral"

    # Gap analysis
    gaps: list[dict[str, Any]] = Field(default_factory=list)
    strengths: list[Any] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)

    # Planning & remediation
    planned_actions: list[dict[str, Any]] = Field(default_factory=list)
    remediation: Any = Field(default_factory=list)
    remediation_outputs: dict[str, Any] = Field(default_factory=dict)
    remediation_results: list[dict[str, Any]] = Field(default_factory=list)

    # Validation loop tracking (Law 5: Feedback Loop Autonomy)
    validation_errors: list[str] = Field(default_factory=list)
    repair_attempts: int = 0
    max_repairs: int = 3

    # Anomaly detection
    anomalies: dict[str, Any] = Field(default_factory=dict)
    predicted_geo_score: float | None = None

    # Report
    report: dict[str, Any] = Field(default_factory=dict)

    # Observability
    step_log: list[dict[str, Any]] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    correlation_id: str = ""

    @model_validator(mode="before")
    @classmethod
    def check_brand_and_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Clean None values to allow defaults to kick in
            for k in list(data.keys()):
                if data[k] is None:
                    del data[k]

            # Fallbacks for brand name
            brand = data.get("brand_name") or data.get("brand") or data.get("business_name")
            if not brand:
                raise ValueError("Brand name is required")
            data["brand_name"] = brand
            data["brand"] = brand
            data["business_name"] = brand

            # Default values
            if "category" not in data:
                data["category"] = "business"
            if "city" not in data:
                data["city"] = "Islamabad"
        return data

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        if key == "brand":
            return self.brand_name
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "brand":
            self.brand_name = value
        elif hasattr(self, key):
            setattr(self, key, value)
        else:
            object.__setattr__(self, key, value)

    def __contains__(self, key: str) -> bool:
        if key == "brand":
            return True
        return hasattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return list(self.model_fields.keys()) + ["brand"]

