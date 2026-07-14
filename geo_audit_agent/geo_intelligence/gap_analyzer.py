def analyze_gap(client_fingerprint: dict, competitor_fingerprint: dict):
    """
    Compares two fingerprints and identifies missing elements.
    """
    missing_keywords = set(competitor_fingerprint.get('keywords', [])) - set(client_fingerprint.get('keywords', []))
    missing_schemas = set(competitor_fingerprint.get('schema_types', [])) - set(client_fingerprint.get('schema_types', []))

    gaps = []
    if missing_keywords:
        gaps.append({"type": "Content Gap", "details": f"Missing top keywords: {list(missing_keywords)[:5]}"})
    if missing_schemas:
        gaps.append({"type": "Schema Gap", "details": f"Competitor uses these schema types you lack: {list(missing_schemas)}"})
    if competitor_fingerprint.get('has_whitepaper') and not client_fingerprint.get('has_whitepaper'):
        gaps.append({"type": "Authority Gap", "details": "Competitor has technical whitepapers; you do not."})

    return gaps
