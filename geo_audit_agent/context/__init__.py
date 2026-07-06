from geo_audit_agent.context import (
    compression_layer,
    fusion_layer,
    intent_classifier,
    prompt_builder,
    reranker,
    validation_layer,
    vector_store,
)


def build_context(query: str, *, brand=None, industry=None, memory=None,
                  live_metrics=None, history=None, agent_state=None,
                  system_role="You are the GEO Copilot."):
    intent = intent_classifier.classify(query)
    retrieved = vector_store.search(query, brand=brand, industry=industry, top_k=20)
    retrieved = reranker.rerank(query, retrieved, top_n=5)
    bundle = fusion_layer.fuse(query=query, retrieved=retrieved, memory=memory or [],
        business_rules=[r.name for r in _active_rules()], live_metrics=live_metrics or {},
        history=history or [], agent_state=agent_state or {})
    bundle = compression_layer.compress(bundle)
    validation = validation_layer.validate(bundle)
    prompt = prompt_builder.build_prompt(bundle, system_role)
    return {"intent": intent, "prompt": prompt, "bundle": bundle, "validation": validation}


def _active_rules():
    from geo_audit_agent.policy.rules import RULES
    return RULES
