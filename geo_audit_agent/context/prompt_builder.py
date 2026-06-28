def build_prompt(bundle: dict, system_role: str) -> str:
    """Assemble the final prompt. LlamaIndex PromptTemplate if available,
    else a deterministic string template (offline-safe)."""
    evidence = "\n".join(f"- {e}" for e in bundle.get("evidence", [])) or "(none)"
    memory = "\n".join(f"- {m}" for m in bundle.get("memory", [])) or "(none)"
    metrics = bundle.get("live_metrics", {})
    try:
        from llama_index.core import PromptTemplate
        tmpl = PromptTemplate(
            "{role}\n\n## Evidence\n{evidence}\n\n## Memory\n{memory}\n\n"
            "## Live metrics\n{metrics}\n\n## Question\n{query}\n")
        return tmpl.format(role=system_role, evidence=evidence, memory=memory,
                           metrics=metrics, query=bundle["query"])
    except Exception:
        return (f"{system_role}\n\n## Evidence\n{evidence}\n\n## Memory\n{memory}"
                f"\n\n## Live metrics\n{metrics}\n\n## Question\n{bundle['query']}\n")
