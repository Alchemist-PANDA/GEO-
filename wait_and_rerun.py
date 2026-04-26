import time
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from geo_audit_agent.agent import build_geo_audit_agent

# Add current dir to path for imports
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_and_rerun():
    brand = "Burger Hub"
    category = "fast food"
    city = "Islamabad"

    production_wait_hours = 48
    test_wait_seconds = 10

    now = datetime.now()
    future = now + timedelta(hours=production_wait_hours)

    logger.info("="*50)
    logger.info("PRODUCTION SIMULATION")
    logger.info(f"In production, we would wait {production_wait_hours} hours.")
    logger.info(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Re-audit would run at: {future.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"MOCKING WAIT: Sleeping for {test_wait_seconds} seconds for testing purposes...")
    logger.info("="*50)

    time.sleep(test_wait_seconds)

    logger.info("Starting post-remediation audit...")
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

        # Save post-remediation results
        with open("post_remediation_audit.json", "w") as f:
            json.dump(results, f, indent=4)

        logger.info("Post-remediation audit completed.")
        return results
    except Exception as e:
        logger.error(f"Post-remediation audit failed: {e}")
        return None

if __name__ == "__main__":
    wait_and_rerun()
