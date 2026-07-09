import asyncio
import datetime
import logging
import os
import random
import time
from typing import Any

import yaml

from geo_audit_agent.testing.gemini_client import APIError, RateLimitError, generate_content_async
from geo_audit_agent.testing.key_manager import GeminiKeyManager
from geo_audit_agent.testing.progress_tracker import ProgressTracker
from geo_audit_agent.testing.storage import load_completed_test_ids, write_result_jsonl

logger = logging.getLogger(__name__)

KNOWN_COMPETITORS = [
    "Burger Lab", "Howdy", "Hardee's", "KFC", "McDonald's",
    "Burger King", "Daily Deli", "OPTP", "Johnny & Jugnu",
    "Burger Hub", "Burger Fest", "Classic Burger"
]

class MegVisibilityTester:
    def __init__(self, config_path: str, output_path: str, delay: float = 1.0, resume: bool = False, tests_per_city: int = 20):
        self.config = self._load_config(config_path)
        self.output_path = output_path
        self.delay = delay
        self.resume = resume
        self.tests_per_city = tests_per_city

        self.key_manager = GeminiKeyManager()
        self.model = self.config.get("model", "gemma-4-31b-it")
        self.brand = self.config.get("brand", "MEG Burger")
        self.cities = self.config.get("cities", [])
        self.templates = self.config.get("prompts", [])

        # Load completed test cases if resuming
        self.completed_ids: set[str] = set()
        if self.resume:
            self.completed_ids = load_completed_test_ids(output_path)

    def _load_config(self, config_path: str) -> dict[str, Any]:
        if os.path.exists(config_path):
            try:
                with open(config_path, encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Failed to load YAML config from {config_path}: {e}")
        return {}

    def _generate_test_cases(self) -> list[dict[str, Any]]:
        """Generates all combinations of city, prompt template, and variants."""
        test_cases = []

        for city in self.cities:
            city_cases = []
            for prompt_idx, template in enumerate(self.templates, 1):
                # Variant 1: standard template
                prompt_text_1 = template.format(city=city)
                city_cases.append({
                    "test_id": f"MEG_{city[:3].upper()}_{prompt_idx:03d}_V1",
                    "city": city,
                    "prompt_id": prompt_idx,
                    "prompt": prompt_text_1,
                    "variant": 1
                })

                # Variant 2: slightly altered template (e.g. adding local details or punctuation)
                prompt_text_2 = template.format(city=city).replace("?", " right now?")
                city_cases.append({
                    "test_id": f"MEG_{city[:3].upper()}_{prompt_idx:03d}_V2",
                    "city": city,
                    "prompt_id": prompt_idx,
                    "prompt": prompt_text_2,
                    "variant": 2
                })

            # Limit the generated tests per city
            test_cases.extend(city_cases[:self.tests_per_city])

        return test_cases

    def _analyze_response(self, text: str) -> dict[str, Any]:
        """Performs citation, sentiment, and competitor analysis on the text response."""
        text_lower = text.lower()
        citation_found = "meg burger" in text_lower

        citation_text = ""
        citation_position = 0
        sentiment = "none"
        confidence_score = 0.0

        # Competitors mentioned
        competitors_mentioned = []
        for comp in KNOWN_COMPETITORS:
            if comp.lower() in text_lower:
                competitors_mentioned.append(comp)

        if citation_found:
            citation_text = "MEG Burger"

            # Find mention position relative to competitors
            meg_index = text_lower.find("meg burger")
            position = 1
            for comp in KNOWN_COMPETITORS:
                comp_idx = text_lower.find(comp.lower())
                if comp_idx != -1 and comp_idx < meg_index:
                    position += 1
            citation_position = position

            # Simple keyword sentiment analyzer
            positive_words = ["best", "love", "popular", "great", "excellent", "delicious", "recommend", "tasty"]
            negative_words = ["bad", "worst", "avoid", "poor", "average", "dislike", "overrated"]

            pos_count = sum(1 for w in positive_words if w in text_lower)
            neg_count = sum(1 for w in negative_words if w in text_lower)

            if pos_count > neg_count:
                sentiment = "positive"
            elif neg_count > pos_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            # Confidence score calculation
            score = 0.5
            if citation_position == 1:
                score += 0.2
            if sentiment == "positive":
                score += 0.2
            if text_lower.count("meg burger") > 1:
                score += 0.1
            confidence_score = round(min(1.0, score), 2)

        return {
            "citation_found": citation_found,
            "citation_text": citation_text,
            "citation_position": citation_position,
            "sentiment": sentiment,
            "confidence_score": confidence_score,
            "competitors_mentioned": competitors_mentioned
        }

    async def _execute_single_test(self, semaphore: asyncio.Semaphore, test_case: dict[str, Any], progress: ProgressTracker):
        test_id = test_case["test_id"]

        # Skip if already completed (resume mode)
        if test_id in self.completed_ids:
            # We don't log skipped ones to console to keep output tidy, but we increment progress tracker
            progress.completed_count += 1
            return

        async with semaphore:
            retries = 3
            backoff = 2.0

            for attempt in range(retries):
                # Rotate key
                api_key = self.key_manager.get_next_key()
                key_name = self.key_manager.get_key_name(api_key)
                start_time = time.time()

                try:
                    # Optional delay per key to respect rate limits
                    if self.delay > 0:
                        await asyncio.sleep(random.uniform(self.delay * 0.5, self.delay * 1.5))

                    text, raw_result = await generate_content_async(
                        prompt=test_case["prompt"],
                        model=self.model,
                        api_key=api_key
                    )

                    elapsed_ms = int((time.time() - start_time) * 1000)
                    analysis = self._analyze_response(text)

                    result_record = {
                        "test_id": test_id,
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "brand": self.brand,
                        "category": "fast food",
                        "city": test_case["city"],
                        "prompt": test_case["prompt"],
                        "prompt_id": test_case["prompt_id"],
                        "variant": test_case["variant"],
                        "api_key_used": key_name,
                        "model": self.model,
                        "response": text,
                        "citation_found": analysis["citation_found"],
                        "citation_text": analysis["citation_text"],
                        "citation_position": analysis["citation_position"],
                        "sentiment": analysis["sentiment"],
                        "confidence_score": analysis["confidence_score"],
                        "response_time_ms": elapsed_ms,
                        "tokens_used": len(text.split()) + len(test_case["prompt"].split()),  # approximation
                        "competitors_mentioned": analysis["competitors_mentioned"],
                        "status": "success"
                    }

                    # Store immediately to JSONL
                    write_result_jsonl(self.output_path, result_record)

                    # Log real-time progress
                    progress.log_progress(
                        city=test_case["city"],
                        prompt_id=test_case["prompt_id"],
                        status="SUCCESS",
                        citation_found=analysis["citation_found"],
                        confidence=analysis["confidence_score"]
                    )
                    return

                except RateLimitError:
                    self.key_manager.mark_failed(api_key)
                    if attempt == retries - 1:
                        # Log final failure for this test case
                        logger.error(f"Test case {test_id} failed after {retries} rate limit attempts.")
                        break
                    # Wait and try again
                    await asyncio.sleep(backoff)
                    backoff *= 2.0

                except APIError as e:
                    logger.warning(f"API Error (Attempt {attempt+1}/{retries}) on key {key_name}: {e}")
                    if attempt == retries - 1:
                        break
                    await asyncio.sleep(backoff)
                    backoff *= 2.0

            # Record failed run
            result_record = {
                "test_id": test_id,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "brand": self.brand,
                "city": test_case["city"],
                "prompt": test_case["prompt"],
                "prompt_id": test_case["prompt_id"],
                "variant": test_case["variant"],
                "status": "error",
                "error_message": "Failed all retry attempts due to API or rate limit errors."
            }
            write_result_jsonl(self.output_path, result_record)
            progress.log_progress(
                city=test_case["city"],
                prompt_id=test_case["prompt_id"],
                status="FAILED",
                citation_found=False,
                confidence=0.0
            )

    async def run_tester_async(self, concurrency_limit: int = 5):
        test_cases = self._generate_test_cases()
        total_runs = len(test_cases)

        # Adjust total runs in tracker if resuming
        tracker = ProgressTracker(total_runs)
        if self.resume:
            logger.info(f"Loaded {len(self.completed_ids)} completed test cases. Resuming remaining {total_runs - len(self.completed_ids)} tests.")

        semaphore = asyncio.Semaphore(concurrency_limit)

        print("\nStarting MEG Burger Gemini Visibility Tester...")
        print(f"Model: {self.model} | Concurrency: {concurrency_limit} | Total Test Cases: {total_runs}\n")

        # Schedule all tests as tasks
        tasks = [
            self._execute_single_test(semaphore, case, tracker)
            for case in test_cases
        ]

        await asyncio.gather(*tasks)
        print("\n All visibility tests completed successfully!")
