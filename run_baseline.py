import json
import logging
import sys
import os
from geo_audit_agent.agent import build_geo_audit_agent

# Add current dir to path for imports
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_baseline():
    brand = "Burger Hub"
    category = "fast food"
    city = "Islamabad"

    logger.info(f"Running baseline audit for {brand} in {city}...")
    agent = build_geo_audit_agent()

    inputs = {
        "brand_name": brand,
        "category": category,
        "city": city,
        "gaps": [],
        "planned_actions": [],
        "remediation_results": []
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
        with open("geo_remediation_burger_hub.json", "w") as f:
            json.dump(remediation_data, f, indent=4)

        logger.info("Baseline audit completed and results saved.")
        return results
    except Exception as e:
        logger.error(f"Baseline audit failed: {e}")
        return None

if __name__ == "__main__":
    run_baseline()
