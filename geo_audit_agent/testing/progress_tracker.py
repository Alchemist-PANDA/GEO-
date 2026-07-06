import json
import os
import logging
from collections import Counter
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ProgressTracker:
    def __init__(self, total_tests: int):
        self.total_tests = total_tests
        self.completed_count = 0
        self.citation_count = 0
    
    def log_progress(self, city: str, prompt_id: int, status: str, citation_found: bool, confidence: float):
        self.completed_count += 1
        if citation_found:
            self.citation_count += 1
        
        cite_str = "YES" if citation_found else "NO"
        percentage = (self.completed_count / self.total_tests) * 100
        
        print(
            f"[{self.completed_count}/{self.total_tests}] {percentage:5.1f}% | "
            f"City: {city:12} | Prompt: {prompt_id:2d} | Status: {status:7} | "
            f"Cite: {cite_str:3} | Conf: {confidence:.2f}"
        )


def generate_summary_report(results_file: str) -> str:
    """Reads all completed JSONL records and generates a summary report."""
    if not os.path.exists(results_file):
        return "No results found to generate report."
    
    records: List[Dict[str, Any]] = []
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    
    # Filter only successful tests for metrics
    success_records = [r for r in records if r.get("status") == "success"]
    total_runs = len(success_records)
    if total_runs == 0:
        return "No successful test records found to generate metrics."
    
    cites_found = sum(1 for r in success_records if r.get("citation_found") is True)
    citation_rate = (cites_found / total_runs) * 100
    avg_confidence = sum(r.get("confidence_score", 0.0) for r in success_records) / total_runs
    
    # City statistics
    city_stats = {}
    for r in success_records:
        city = r["city"]
        if city not in city_stats:
            city_stats[city] = {"total": 0, "cites": 0}
        city_stats[city]["total"] += 1
        if r.get("citation_found") is True:
            city_stats[city]["cites"] += 1
            
    # Competitor mentions
    competitor_counter = Counter()
    for r in success_records:
        competitors = r.get("competitors_mentioned", [])
        for comp in competitors:
            competitor_counter[comp] += 1
            
    # Sort cities by citation rate (highest first)
    sorted_cities = []
    for city, stats in city_stats.items():
        rate = (stats["cites"] / stats["total"]) * 100
        sorted_cities.append((city, rate, stats["cites"], stats["total"]))
    sorted_cities.sort(key=lambda x: x[1], reverse=True)
    
    # Format top and bottom cities
    top_cities = sorted_cities[:3]
    bottom_cities = sorted_cities[-3:]
    
    # Build text report
    lines = []
    lines.append("=" * 60)
    lines.append("MEG Burger - Gemini Visibility Test Report")
    lines.append("=" * 60)
    lines.append(f"Total Successful Tests: {total_runs}")
    lines.append(f"Total Cites Found:      {cites_found}")
    lines.append(f"Overall Citation Rate:  {citation_rate:.1f}%")
    lines.append(f"Average Confidence:      {avg_confidence:.2f}")
    lines.append("-" * 60)
    
    lines.append("City Performance Breakdown:")
    for city, rate, cites, total in sorted_cities:
        lines.append(f"  - {city:12}: {rate:5.1f}% ({cites}/{total})")
    lines.append("-" * 60)
    
    lines.append("Top Performing Cities:")
    for city, rate, cites, total in top_cities:
        lines.append(f"  - {city:12}: {rate:5.1f}% ({cites}/{total})")
    lines.append("-" * 60)
    
    lines.append("Bottom Performing Cities:")
    for city, rate, cites, total in bottom_cities:
        lines.append(f"  - {city:12}: {rate:5.1f}% ({cites}/{total})")
    lines.append("-" * 60)
    
    lines.append("Competitors Mentioned:")
    if competitor_counter:
        for comp, count in competitor_counter.most_common(10):
            lines.append(f"  - {comp:18}: {count} times")
    else:
        lines.append("  - None detected.")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def write_summary_json(results_file: str, summary_file: str):
    """Calculates statistics and writes a summary JSON file."""
    if not os.path.exists(results_file):
        return
    
    records = []
    with open(results_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    
    success_records = [r for r in records if r.get("status") == "success"]
    if not success_records:
        return
    
    cites = sum(1 for r in success_records if r.get("citation_found") is True)
    total = len(success_records)
    
    # Calculate competitor mentions count
    competitors = Counter()
    for r in success_records:
        for c in r.get("competitors_mentioned", []):
            competitors[c] += 1
            
    # Calculate city breakdown
    city_rates = {}
    for r in success_records:
        city = r["city"]
        if city not in city_rates:
            city_rates[city] = {"total": 0, "cites": 0}
        city_rates[city]["total"] += 1
        if r.get("citation_found") is True:
            city_rates[city]["cites"] += 1
            
    city_breakdown = {}
    for city, stats in city_rates.items():
        city_breakdown[city] = {
            "citation_rate": round((stats["cites"] / stats["total"]) * 100, 2),
            "cites_found": stats["cites"],
            "total_runs": stats["total"]
        }
        
    summary_data = {
        "brand": "MEG Burger",
        "total_successful_runs": total,
        "total_cites_found": cites,
        "overall_citation_rate": round((cites / total) * 100, 2),
        "average_confidence": round(sum(r.get("confidence_score", 0.0) for r in success_records) / total, 2),
        "city_breakdown": city_breakdown,
        "competitor_mentions": dict(competitors.most_common(10))
    }
    
    # Ensure directory exists
    dir_name = os.path.dirname(summary_file)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4)
