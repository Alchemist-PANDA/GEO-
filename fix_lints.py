import os

replacements = {
    'geo_audit_agent/actions/mapper.py': [
        ('seen.add(aid); chosen.append(REGISTRY[aid])', 'seen.add(aid)\n                        chosen.append(REGISTRY[aid])')
    ],
    'geo_audit_agent/agents/inspector_agent.py': [
        ('checks.update(sem[\"checks\"]); issues.extend(sem[\"issues\"])', 'checks.update(sem[\"checks\"])\n            issues.extend(sem[\"issues\"])'),
        ('issues.append(\"output_quality:empty\"); return False', 'issues.append(\"output_quality:empty\")\n            return False'),
        ('issues.append(\"output_quality:prompt_leak\"); return False', 'issues.append(\"output_quality:prompt_leak\")\n            return False'),
        ('issues.append(\"evidence:missing\"); return False', 'issues.append(\"evidence:missing\")\n            return False'),
        ('issues.append(f\"tool:{call.get(''name'')}_failed\"); return False', 'issues.append(f\"tool:{call.get(''name'')}_failed\")\n                return False'),
        ('issues.append(\"context:over_budget\"); return False', 'issues.append(\"context:over_budget\")\n            return False'),
        ('issues.append(\"governance:secret_leak\"); return False', 'issues.append(\"governance:secret_leak\")\n            return False'),
        ('if data.get(\"hallucination\"):       issues.append(\"hallucination:flagged\")', 'if data.get(\"hallucination\"):\n            issues.append(\"hallucination:flagged\")'),
        ('if data.get(\"unsupported_claims\"):  issues.append(\"unsupported_claims\")', 'if data.get(\"unsupported_claims\"):\n            issues.append(\"unsupported_claims\")')
    ],
    'geo_audit_agent/context/compression_layer.py': [
        ('seen.add(key); deduped.append(txt)', 'seen.add(key)\n            deduped.append(txt)'),
        ('if used > token_budget: break', 'if used > token_budget:\n                break')
    ],
    'geo_audit_agent/context/vector_store.py': [
        ('if brand:    must.append(FieldCondition(key=\"brand\", match=MatchValue(value=brand)))', 'if brand:\n        must.append(FieldCondition(key=\"brand\", match=MatchValue(value=brand)))'),
        ('if industry: must.append(FieldCondition(key=\"industry\", match=MatchValue(value=industry)))', 'if industry:\n        must.append(FieldCondition(key=\"industry\", match=MatchValue(value=industry)))')
    ],
    'geo_audit_agent/copilot/engine.py': [
        ('{\"role\": \"assistant\", \"content\": \"Understood, I am retaining the context of our previous discussion.\"},', '{\"role\": \"assistant\", \"content\": \"Understood, I am retaining the context of our previous discussion.\"}')
    ],
    'geo_audit_agent/evaluation/deep_eval.py': [
        ('M.measure(tc); out[M.__class__.__name__] = M.score', 'M.measure(tc)\n        out[M.__class__.__name__] = M.score')
    ],
    'geo_audit_agent/guardrails/types.py': [
        ('LOW = \"low\"; MEDIUM = \"medium\"; HIGH = \"high\"; CRITICAL = \"critical\"', 'LOW = \"low\"\n    MEDIUM = \"medium\"\n    HIGH = \"high\"\n    CRITICAL = \"critical\"')
    ],
    'geo_audit_agent/memory/memory_guardrails.py': [
        ('if _SENSITIVE.search(text):           return False, \"sensitive_information\"', 'if _SENSITIVE.search(text):\n        return False, \"sensitive_information\"'),
        ('if _TEMP.search(text):                return False, \"temporary_information\"', 'if _TEMP.search(text):\n        return False, \"temporary_information\"'),
        ('if meta.get(\"hallucination_risk\"):    return False, \"possible_hallucination\"', 'if meta.get(\"hallucination_risk\"):\n        return False, \"possible_hallucination\"'),
        ('if len(text) < 8:                     return False, \"too_trivial\"', 'if len(text) < 8:\n        return False, \"too_trivial\"')
    ],
    'geo_audit_agent/orchestration/langgraph_workflow.py': [
        ('state.context = ctx; state.intent = ctx[\"intent\"]', 'state.context = ctx\n    state.intent = ctx[\"intent\"]'),
        ('state.gaps = out.get(\"gaps\", []); state.next_agent = \"inspector\"; return state', 'state.gaps = out.get(\"gaps\", [])\n    state.next_agent = \"inspector\"\n    return state'),
        ('state.next_agent = \"inspector\"; return state', 'state.next_agent = \"inspector\"\n    return state'),
        ('a = ActionAgent(); state = a.plan(state); state = a.execute(state)', 'a = ActionAgent()\n    state = a.plan(state)\n    state = a.execute(state)')
    ],
    'geo_audit_agent/self_improvement/canary_rollout.py': [
        ('def promote(agent_id):   _r.set(f\"config:{agent_id}\", _r.get(f\"canary:{agent_id}\")); _r.delete(f\"canary:{agent_id}\")', 'def promote(agent_id):\n    _r.set(f\"config:{agent_id}\", _r.get(f\"canary:{agent_id}\"))\n    _r.delete(f\"canary:{agent_id}\")'),
        ('def rollback(agent_id):  _r.delete(f\"canary:{agent_id}\")     # instant revert to stable', 'def rollback(agent_id):\n    _r.delete(f\"canary:{agent_id}\")     # instant revert to stable')
    ],
    'geo_audit_agent/self_improvement/improvement_proposer.py': [
        ('s.add(p); s.commit(); s.refresh(p)', 's.add(p)\n        s.commit()\n        s.refresh(p)')
    ],
    'geo_audit_agent/self_improvement/outcome_tracker.py': [
        ('row.outcome = outcome; row.score = score; s.add(row); s.commit()', 'row.outcome = outcome\n            row.score = score\n            s.add(row)\n            s.commit()')
    ]
}

for fp, reps in replacements.items():
    if not os.path.exists(fp): continue
    with open(fp, \"r\", encoding=\"utf-8\") as f:
        content = f.read()
    for old, new in reps:
        content = content.replace(old, new)
    with open(fp, \"w\", encoding=\"utf-8\") as f:
        f.write(content)

print(\"Done\")
