import json
import logging
import argparse
from geo_audit_agent.agent import build_geo_audit_agent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_baseline(brand: str, category: str, city: str):
    logger.info(f"Running baseline audit for {brand} in {city}...")
    agent = build_geo_audit_agent()

    inputs = {
        "brand_name": brand,
        "category": category,
        "city": city,
        "gaps": [],
        "planned_actions": [],
        "remediation_results": [],
        "error": None
    }

    try:
        results = agent.invoke(inputs)

        # Save baseline
        with open("pre_remediation_audit.json", "w") as f:
            json.dump(results, f, indent=4)

        # Also extract remediation results for deployment step
        remediation_data = {
            "brand": brand,
            "remediation_results": results.get("remediation_results", [])
        }
        safe_name = brand.lower().replace(" ", "_")
        with open(f"geo_remediation_{safe_name}.json", "w") as f:
            json.dump(remediation_data, f, indent=4)

        logger.info("Baseline audit completed and results saved.")
        return results
    except Exception as e:
        logger.exception(f"Baseline audit failed: {e}")
        return None

if __name__ == "__main__":
    # Issue #27: accept CLI arguments with backward-compatible defaults
    parser = argparse.ArgumentParser(description="Run a baseline GEO audit.")
    parser.add_argument("--brand", default="Burger Hub", help="Brand name to audit (default: Burger Hub)")
    parser.add_argument("--category", default="fast food", help="Business category (default: fast food)")
    parser.add_argument("--city", default="Islamabad", help="City name (default: Islamabad)")
    args = parser.parse_args()

    run_baseline(args.brand, args.category, args.city)
