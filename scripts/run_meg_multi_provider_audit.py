import datetime
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

# Load .env
load_dotenv()

# Gemini key rotation pool
gemini_keys = []
for i in range(1, 7):
    val = os.getenv(f"GOOGLE_API_KEY_{i}")
    if val:
        gemini_keys.append(val)
gemini_key_index = 0

# Providers client functions
def get_provider_credentials(provider: str):
    """Retrieve API key from env or system environment."""
    if provider == "gemini":
        global gemini_key_index
        if not gemini_keys:
            return None, "No keys found"
        key = gemini_keys[gemini_key_index % len(gemini_keys)]
        gemini_key_index += 1
        return key, None
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        return key, None
    elif provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        return key, None
    elif provider == "groq":
        key = os.getenv("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        return key, None
    return None, f"Unknown provider {provider}"

def list_models_for_provider(provider: str, client: httpx.Client) -> dict:
    """Call models list endpoint for the given provider."""
    key, err = get_provider_credentials(provider)
    if not key or "your" in key.lower() or "placeholder" in key.lower():
        return {"status": "error", "message": f"API Key for {provider} is unconfigured or a placeholder."}

    try:
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
            response = client.get(url, timeout=30.0)
        elif provider == "openai":
            url = "https://api.openai.com/v1/models"
            response = client.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=30.0)
        elif provider == "anthropic":
            url = "https://api.anthropic.com/v1/models"
            response = client.get(url, headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01"
            }, timeout=30.0)
        elif provider == "groq":
            url = "https://api.groq.com/openai/v1/models"
            response = client.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=30.0)
        else:
            return {"status": "error", "message": f"Unsupported provider: {provider}"}

        return {
            "status": "success",
            "http_status": response.status_code,
            "raw_response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {"status": "error", "message": f"Exception occurred: {str(e)} ({type(e).__name__})"}

def execute_single_call(provider: str, model: str, prompt: str, client: httpx.Client, temperature: float = 0.0, max_tokens: int = 300) -> dict:
    """Run a single content generation call to a specific provider and model."""
    key, err = get_provider_credentials(provider)
    if not key or "your" in key.lower() or "placeholder" in key.lower():
         return {"status": "error", "message": f"API Key for {provider} is placeholder/unconfigured."}

    try:
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
            }
            response = client.post(url, json=data, timeout=60.0)

        elif provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            response = client.post(url, json=data, headers=headers, timeout=60.0)

        elif provider == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            response = client.post(url, json=data, headers=headers, timeout=60.0)

        elif provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            response = client.post(url, json=data, headers=headers, timeout=60.0)
        else:
            return {"status": "error", "message": f"Unsupported provider {provider}"}

        res_json = None
        extracted_text = None

        if response.status_code == 200:
            res_json = response.json()
            if provider == "gemini":
                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text_parts = [p.get("text", "") for p in parts if not p.get("thought")]
                        extracted_text = "".join(text_parts) if text_parts else parts[0].get("text", "")
            elif provider == "openai":
                extracted_text = res_json["choices"][0]["message"]["content"]
            elif provider == "anthropic":
                extracted_text = res_json["content"][0]["text"]
            elif provider == "groq":
                extracted_text = res_json["choices"][0]["message"]["content"]

        return {
            "status": "success" if response.status_code == 200 and extracted_text is not None else "fail",
            "http_status": response.status_code,
            "raw_response": res_json if response.status_code == 200 else response.text,
            "extracted_text": extracted_text,
            "error_message": response.text if response.status_code != 200 else (None if extracted_text is not None else "Parsing path failed")
        }

    except Exception as e:
        return {"status": "error", "message": f"Exception occurred: {str(e)} ({type(e).__name__})"}

def parse_retry_after(provider: str, response_text: str, headers: dict) -> float:
    """Parse retry-after headers or payload parameters if rate-limited (429)."""
    # Check headers
    retry_header = headers.get("retry-after")
    if retry_header:
        try:
            return float(retry_header)
        except ValueError:
            pass

    # Check payload specifics
    if provider == "groq":
        try:
            # Check for body strings like "Please retry in X.XXs"
            data = json.loads(response_text)
            msg = data.get("error", {}).get("message", "")
            if "please retry in" in msg.lower():
                parts = msg.lower().split("please retry in ")
                if len(parts) > 1:
                    sec_str = parts[1].split("s")[0].strip()
                    return float(sec_str)
        except Exception:
            pass

    if provider == "gemini":
        try:
            data = json.loads(response_text)
            msg = data.get("error", {}).get("message", "")
            if "please retry in" in msg.lower():
                parts = msg.lower().split("please retry in ")
                if len(parts) > 1:
                    sec_str = parts[1].split("s")[0].strip()
                    return float(sec_str)
        except Exception:
            pass

    return 10.0 # Default fallback wait if 429 occurs

def run_batch_audit(provider: str, model: str, test_cases: list, output_path: Path, pacing_delay: float):
    """Run batch audit over 100 queries for a specific provider/model."""
    print(f"Starting batch run for provider={provider}, model={model} -> {output_path}", flush=True)

    # Initialize output file
    with open(output_path, "w", encoding="utf-8") as f:
        pass

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
                # Retrieve key (rotates for gemini, single key for others)
                key, err = get_provider_credentials(provider)
                if not key or "your" in key.lower() or "placeholder" in key.lower():
                    last_status = 401
                    last_error = f"API key is unconfigured placeholder for {provider}."
                    break

                # Use key name for Gemini logging, else provider name
                last_key_used = f"GOOGLE_API_KEY_{gemini_key_index}" if provider == "gemini" else f"{provider.upper()}_API_KEY"

                try:
                    if provider == "gemini":
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                        data = {
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": 0.2}
                        }
                        response = client.post(url, json=data)

                    elif provider == "openai":
                        url = "https://api.openai.com/v1/chat/completions"
                        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                        data = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
                        response = client.post(url, json=data, headers=headers)

                    elif provider == "anthropic":
                        url = "https://api.anthropic.com/v1/messages"
                        headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
                        data = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 1000}
                        response = client.post(url, json=data, headers=headers)

                    elif provider == "groq":
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                        data = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
                        response = client.post(url, json=data, headers=headers)
                    else:
                        raise ValueError(f"Unknown provider {provider}")

                    last_status = response.status_code

                    if response.status_code == 200:
                        res_json = response.json()
                        raw_api_resp = res_json

                        if provider == "gemini":
                            candidates = res_json.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    text_parts = [p.get("text", "") for p in parts if not p.get("thought")]
                                    text = "".join(text_parts) if text_parts else parts[0].get("text", "")
                                    last_response_text = text
                                    success = True
                                    last_error = None
                                    break
                        elif provider == "openai":
                            last_response_text = res_json["choices"][0]["message"]["content"]
                            success = True
                            last_error = None
                            break
                        elif provider == "anthropic":
                            last_response_text = res_json["content"][0]["text"]
                            success = True
                            last_error = None
                            break
                        elif provider == "groq":
                            last_response_text = res_json["choices"][0]["message"]["content"]
                            success = True
                            last_error = None
                            break
                    else:
                        last_error = f"API returned status {response.status_code}: {response.text}"
                        if response.status_code == 429:
                            # Handle rate limit backoff
                            wait_sec = parse_retry_after(provider, response.text, dict(response.headers))
                            print(f"[{test_id}] Rate limited (429). Sleeping {wait_sec:.2f}s before retry...", file=sys.stderr, flush=True)
                            time.sleep(wait_sec + 1.0)

                except Exception as e:
                    last_status = 0
                    last_error = f"Request Exception: {str(e)} ({type(e).__name__})"

                # Print attempt failure to stderr
                print(f"[{test_id}] Attempt {attempt+1} failed with key {last_key_used} (Status {last_status}): {last_error}.", file=sys.stderr, flush=True)

                if attempt < attempts - 1 and last_status != 429:
                    # Retry delay
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

            with open(output_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

            print(f"[{idx:03d}/100] Case {test_id} written. Success={success}, Key={last_key_used}, Status={last_status}", flush=True)

            # Pacing delay between queries
            time.sleep(pacing_delay)

if __name__ == '__main__':
    # Parse CLI args manually
    args = sys.argv[1:]

    cities = ["Islamabad", "Lahore", "Karachi", "Rawalpindi", "Peshawar", "Quetta", "Faisalabad", "Multan", "Hyderabad", "Gujranwala"]
    templates = [
        "What is the best burger place in {city}?",
        "Which burger restaurant would you recommend in {city}?",
        "Where can I get a good burger in {city}?",
        "What are the top-rated burger joints in {city}?",
        "If I'm in {city} and craving a burger, where should I go?"
    ]

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

    if "--list-models" in args:
        print("=== STEP 1: DISCOVER AVAILABLE MODELS ===", flush=True)
        with httpx.Client() as client:
            for p in ["gemini", "openai", "anthropic", "groq"]:
                print(f"\n--- Provider: {p.upper()} ---")
                res = list_models_for_provider(p, client)
                if res["status"] == "success":
                    print(f"HTTP Status: {res['http_status']}")
                    # If success, print the first few models or metadata
                    if isinstance(res["raw_response"], dict):
                        models_list = res["raw_response"].get("models") or res["raw_response"].get("data") or []
                        print(f"Found {len(models_list)} models. Details of first 5:")
                        for m in models_list[:5]:
                            print(f"  - Model ID: {m.get('name') or m.get('id')}")
                    else:
                        print(res["raw_response"])
                else:
                    print(f"Error: {res['message']}")

    elif "--test-single" in args:
        print("=== STEP 2 & 3: SINGLE TEST CALL ===", flush=True)
        # Identify targeted models:
        targets = {
            "gemini": "gemini-2.5-flash",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20241022",
            "groq": "llama-3.3-70b-versatile"
        }

        prompt = "What are the best burger joints in Islamabad?"
        with httpx.Client() as client:
            for p, model in targets.items():
                print("\n======================================")
                print(f"PROVIDER: {p.upper()} | MODEL: {model}")
                print("======================================")
                res = execute_single_call(p, model, prompt, client, temperature=0.0, max_tokens=300)
                if res["status"] == "success":
                    print(f"HTTP Status Code: {res['http_status']}")
                    print("\n--- Raw JSON Response Payload ---")
                    print(json.dumps(res["raw_response"], indent=2))
                    print("\n--- Extracted Content Text ---")
                    print(res["extracted_text"])
                else:
                    print("Status: FAILED")
                    print(f"HTTP Status Code: {res.get('http_status')}")
                    print(f"Error Details: {res.get('error_message') or res.get('message')}")

    elif "--run-batch" in args:
        # Check provider argument
        target_provider = None
        for arg in args:
            if arg.startswith("--provider="):
                target_provider = arg.split("=")[1].strip().lower()

        if not target_provider or target_provider not in ["gemini", "openai", "anthropic", "groq"]:
            print("Error: Specify provider with --provider=gemini|openai|anthropic|groq")
            sys.exit(1)

        configs = {
            "gemini": {"model": "gemini-2.5-flash", "pacing": 5.0, "file": "data/meg_test_100_gemini.jsonl"},
            "openai": {"model": "gpt-4o-mini", "pacing": 2.0, "file": "data/meg_test_100_openai.jsonl"},
            "anthropic": {"model": "claude-3-5-sonnet-20241022", "pacing": 3.0, "file": "data/meg_test_100_anthropic.jsonl"},
            "groq": {"model": "llama-3.3-70b-versatile", "pacing": 4.0, "file": "data/meg_test_100_groq.jsonl"}
        }

        cfg = configs[target_provider]
        run_batch_audit(
            provider=target_provider,
            model=cfg["model"],
            test_cases=test_cases,
            output_path=Path(cfg["file"]),
            pacing_delay=cfg["pacing"]
        )
    else:
        print("Usage: python scripts/run_meg_multi_provider_audit.py --list-models | --test-single | --run-batch --provider=<provider>")
