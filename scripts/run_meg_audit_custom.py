import datetime
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

# Load .env
load_dotenv()

# Load keys
keys = []
key_names = []
for i in range(1, 7):
    val = os.getenv(f"GOOGLE_API_KEY_{i}")
    if val:
        keys.append(val)
        key_names.append(f"GOOGLE_API_KEY_{i}")

if len(keys) < 6:
    print(f"Error: Only found {len(keys)} GOOGLE_API_KEY_N variables. Required: 6.")
    sys.exit(1)

# Cities and prompts
cities = ["Islamabad", "Lahore", "Karachi", "Rawalpindi", "Peshawar", "Quetta", "Faisalabad", "Multan", "Hyderabad", "Gujranwala"]
templates = [
    "What is the best burger place in {city}?",
    "Which burger restaurant would you recommend in {city}?",
    "Where can I get a good burger in {city}?",
    "What are the top-rated burger joints in {city}?",
    "If I'm in {city} and craving a burger, where should I go?"
]

# Generate 100 test cases
test_cases = []
for city in cities:
    for p_idx, template in enumerate(templates, 1):
        # Variant 1
        test_cases.append({
            "test_id": f"MEG_{city[:3].upper()}_{p_idx:03d}_V1",
            "city": city,
            "prompt_id": p_idx,
            "variant": 1,
            "prompt": template.format(city=city)
        })
        # Variant 2
        test_cases.append({
            "test_id": f"MEG_{city[:3].upper()}_{p_idx:03d}_V2",
            "city": city,
            "prompt_id": p_idx,
            "variant": 2,
            "prompt": template.format(city=city).replace("?", " right now?")
        })

print(f"Generated {len(test_cases)} test cases.", flush=True)

# Round robin index
key_index = 0

def execute_audit():
    global key_index
    output_file = Path("data/meg_test_100_flash_run.jsonl")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Reset/Create the file
    with open(output_file, "w", encoding="utf-8") as f:
        pass

    # We use gemini-3.5-flash
    model_id = "gemini-2.5-flash"

    with httpx.Client(timeout=60.0) as client:
        for idx, case in enumerate(test_cases, 1):
            test_id = case["test_id"]
            prompt = case["prompt"]
            city = case["city"]
            prompt_id = case["prompt_id"]
            variant = case["variant"]

            success = False
            attempts = 2

            last_status = None
            last_error = None
            last_key_used = None
            last_response_text = None
            raw_api_resp = None

            for attempt in range(attempts):
                # Round-robin key selection
                current_key = keys[key_index % len(keys)]
                current_key_name = key_names[key_index % len(keys)]
                key_index += 1
                last_key_used = current_key_name

                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={current_key}"
                data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2}
                }

                try:
                    response = client.post(url, json=data)
                    last_status = response.status_code

                    if response.status_code == 200:
                        res_json = response.json()
                        raw_api_resp = res_json
                        candidates = res_json.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                # Join all text parts, omitting thought blocks
                                text_parts = [p.get("text", "") for p in parts if not p.get("thought")]
                                text = "".join(text_parts) if text_parts else parts[0].get("text", "")
                                last_response_text = text
                                success = True
                                last_error = None
                                break
                            else:
                                last_error = f"Empty parts list in candidates. Raw: {response.text}"
                        else:
                            last_error = f"No candidates in response. Raw: {response.text}"
                    else:
                        last_error = f"API returned status {response.status_code}: {response.text}"

                except Exception as e:
                    last_status = 0
                    last_error = f"Request Exception: {str(e)} ({type(e).__name__})"

                # Print attempt failure to stderr (flushed)
                print(f"[{test_id}] Attempt {attempt+1} failed with key {current_key_name} (Status {last_status}): {last_error}.", file=sys.stderr, flush=True)

                if attempt < attempts - 1:
                    # Delay 5 seconds between retries
                    time.sleep(5.0)

            # Log results to output file
            record = {
                "test_id": test_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "city": city,
                "prompt_id": prompt_id,
                "variant": variant,
                "prompt": prompt,
                "api_key_used": last_key_used,
                "status_code": last_status,
                "response": last_response_text if success else None,
                "raw_api_response": raw_api_resp,
                "error_message": last_error if not success else None
            }

            with open(output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

            print(f"[{idx:03d}/100] Case {test_id} written. Success={success}, Key={last_key_used}, Status={last_status}", flush=True)

            # Pacing delay: 5.0 seconds between queries to stay below the 15 RPM project-level limit
            time.sleep(5.0)

if __name__ == '__main__':
    execute_audit()
