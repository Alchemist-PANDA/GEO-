from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Metric:
    numerator: int
    denominator: int

    @property
    def value(self) -> float | None:
        return self.numerator / self.denominator if self.denominator else None

    def as_dict(self) -> dict[str, int | float | None]:
        return {"value": self.value, "numerator": self.numerator, "denominator": self.denominator,
                "sample_size": self.denominator}


@dataclass(frozen=True)
class VisibilityMetrics:
    mention_rate: Metric
    recommendation_rate: Metric
    top_three_rate: Metric
    citation_rate: Metric
    provider_coverage: Metric
    prompt_coverage: Metric

    def as_dict(self) -> dict[str, dict[str, int | float | None]]:
        return {name: getattr(self, name).as_dict() for name in self.__dataclass_fields__}


def calculate_visibility_metrics(
    observations: Iterable[dict[str, Any]],
    *,
    expected_providers: Iterable[str] = (),
    expected_prompts: Iterable[str] = (),
) -> VisibilityMetrics:
    rows = [row for row in observations if row.get("mode") in {"live", "cached"} and not row.get("error")]
    total = len(rows)
    providers = {str(row.get("provider")) for row in rows if row.get("provider")}
    prompts = {str(row.get("prompt_id")) for row in rows if row.get("prompt_id")}
    expected_provider_set = set(expected_providers)
    expected_prompt_set = set(expected_prompts)
    return VisibilityMetrics(
        mention_rate=Metric(sum(bool(row.get("mentioned")) for row in rows), total),
        recommendation_rate=Metric(sum(bool(row.get("recommended")) for row in rows), total),
        top_three_rate=Metric(sum(bool(row.get("mentioned")) and 1 <= int(row.get("position") or 999) <= 3 for row in rows), total),
        citation_rate=Metric(sum(bool(row.get("citation_urls")) for row in rows), total),
        provider_coverage=Metric(len(providers & expected_provider_set), len(expected_provider_set)),
        prompt_coverage=Metric(len(prompts & expected_prompt_set), len(expected_prompt_set)),
    )
