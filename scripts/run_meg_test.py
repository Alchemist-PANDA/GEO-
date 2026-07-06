import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env variables
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

from geo_audit_agent.testing.meg_visibility_tester import MegVisibilityTester
from geo_audit_agent.testing.progress_tracker import generate_summary_report, write_summary_json

# Setup basic logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def parse_args():
    parser = argparse.ArgumentParser(description="MEG Burger Brand Visibility Gemini-Only Tester")
    
    parser.add_argument(
        "--brand", 
        type=str, 
        help="Brand name to test (overrides config)"
    )
    parser.add_argument(
        "--cities", 
        type=str, 
        help="Comma-separated list of cities to test (overrides config)"
    )
    parser.add_argument(
        "--tests-per-city", 
        type=int, 
        default=20,
        help="Number of tests per city (1-20, default: 20)"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=1.0,
        help="Base delay in seconds between API calls to prevent rate limiting (default: 1.0)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/meg_burger_results.jsonl",
        help="Output JSONL results file path (default: data/meg_burger_results.jsonl)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/meg_test_config.yaml",
        help="Configuration YAML file path (default: config/meg_test_config.yaml)"
    )
    parser.add_argument(
        "--resume", 
        action="store_true",
        help="Resume testing using existing output file to skip already completed test IDs"
    )
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Initialize tester
    tester = MegVisibilityTester(
        config_path=args.config,
        output_path=args.output,
        delay=args.delay,
        resume=args.resume,
        tests_per_city=args.tests_per_city
    )
    
    # Override defaults if flags provided
    if args.brand:
        tester.brand = args.brand
    if args.cities:
        tester.cities = [c.strip() for c in args.cities.split(",")]
        
    if not tester.cities:
        print("Error: No target cities specified. Define them in config or pass --cities.")
        sys.exit(1)
        
    # Run async tester
    try:
        asyncio.run(tester.run_tester_async())
    except KeyboardInterrupt:
        print("\nTesting interrupted by user. Progress saved.")
        sys.exit(0)
    except Exception as e:
        print(f"\nExecution error: {e}")
        sys.exit(1)
        
    # Generate and print summary reports
    print("\n" + "=" * 60)
    print("SUMMARY REPORT GENERATION")
    print("=" * 60)
    
    report = generate_summary_report(args.output)
    print(report)
    
    summary_json_path = args.output.replace(".jsonl", "_summary.json")
    write_summary_json(args.output, summary_json_path)
    print(f"\nSummary JSON statistics saved to: {summary_json_path}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
