"""
Wait-and-rerun script for post-remediation audit.

NOTE: This script is for DEVELOPMENT/TESTING only.
In production, use a proper task scheduler (cron, Windows Task Scheduler, Celery)
instead of in-process time.sleep(). A 48-hour sleep will be killed by OS/session timeouts.
"""
import argparse
import json
import logging
import time
from datetime import datetime, timedelta

from geo_audit_agent.agent import build_geo_audit_agent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_and_rerun(brand: str, category: str, city: str):
    production_wait_hours = 48
    test_wait_seconds = 10

    now = datetime.now()
    future = now + timedelta(hours=production_wait_hours)

    logger.info("="*50)
    logger.info("DEVELOPMENT-ONLY MOCK WAIT")
    logger.info(f"In production, use a task scheduler to wait {production_wait_hours} hours.")
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
        "remediation_results": [],
        "error": None
    }

    try:
        results = agent.invoke(inputs)

        # Save post-remediation results
        with open("post_remediation_audit.json", "w") as f:
            json.dump(results, f, indent=4)

        logger.info("Post-remediation audit completed.")
        return results
    except Exception as e:
        logger.exception(f"Post-remediation audit failed: {e}")
        return None

if __name__ == "__main__":
    # Issue #27: accept CLI arguments with backward-compatible defaults
    parser = argparse.ArgumentParser(description="Wait and re-run a post-remediation GEO audit (dev only).")
    parser.add_argument("--brand", default="Burger Hub", help="Brand name to audit (default: Burger Hub)")
    parser.add_argument("--category", default="fast food", help="Business category (default: fast food)")
    parser.add_argument("--city", default="Islamabad", help="City name (default: Islamabad)")
    args = parser.parse_args()

    wait_and_rerun(args.brand, args.category, args.city)
