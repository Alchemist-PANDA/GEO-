from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    output: Any
    error: str | None = None
    tokens_used: int = 0


class BaseTool(ABC):
    name: str
    description: str
    requires_llm: bool = False

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        ...

    def validate_inputs(self, **kwargs) -> bool:
        return True


class JSONLDTool(BaseTool):
    name = "generate_json_ld"
    description = "Generates Schema.org LocalBusiness JSON-LD markup"
    requires_llm = False

    def run(self, brand_name: str, category: str, city: str, **kwargs: Any) -> ToolResult:  # type: ignore[override]
        from geo_audit_agent.geo_remediation_tools import generate_json_ld
        try:
            product_info = {
                "name": brand_name,
                "description": f"A local {category} in {city}",
                "address": city
            }
            output = generate_json_ld(brand_name, product_info)
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class WhitepaperTool(BaseTool):
    name = "draft_technical_whitepaper"
    description = "Generates authority-building technical content"
    requires_llm = True

    def run(self, brand_name: str, category: str, gaps: list, **kwargs: Any) -> ToolResult:  # type: ignore[override]
        from geo_audit_agent.geo_remediation_tools import draft_technical_whitepaper
        try:
            topic = f"GEO visibility optimization for {brand_name} in {category}"
            key_features = [str(g.get("description", g)) if isinstance(g, dict) else str(g) for g in gaps] or ["General visibility factors"]
            output = draft_technical_whitepaper(brand_name, topic, key_features)
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class ReviewTemplateTool(BaseTool):
    name = "generate_review_template"
    description = "Generates review collection email template"
    requires_llm = False

    def run(self, brand_name: str, category: str, city: str, **kwargs: Any) -> ToolResult:  # type: ignore[override]
        from geo_audit_agent.geo_remediation_tools import generate_review_template
        try:
            output = generate_review_template(brand_name=brand_name, category=category, city=city, rating=4.5)
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


TOOL_REGISTRY: Dict[str, BaseTool] = {
    "generate_json_ld": JSONLDTool(),
    "draft_technical_whitepaper": WhitepaperTool(),
    "generate_review_template": ReviewTemplateTool(),
}
