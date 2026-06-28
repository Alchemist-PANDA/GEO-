import re
_TEMP = re.compile(r"\b(today|right now|currently loading|temporary|just now)\b", re.I)
_SENSITIVE = re.compile(r"\b(password|api[_ ]?key|ssn|credit card|secret)\b", re.I)

def allow_memory(text: str, meta: dict) -> tuple[bool, str]:
    if _SENSITIVE.search(text):           
        return False, "sensitive_information"
    if _TEMP.search(text):                
        return False, "temporary_information"
    if meta.get("hallucination_risk"):    
        return False, "possible_hallucination"
    if len(text) < 8:                     
        return False, "too_trivial"
    return True, "ok"
