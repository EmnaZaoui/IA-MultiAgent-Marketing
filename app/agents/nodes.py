from app.agents.state import AgentState
from app.agents.prompts import (
    RESEARCHER_SYSTEM_PROMPT,
    STRATEGIST_SYSTEM_PROMPT,
    COPYWRITER_SYSTEM_PROMPT,
    COMPLIANCE_SYSTEM_PROMPT,
)
from app.agents.llm_client import call_llm_json, LLMError
from app.services.vectorstore_service import search_features


def researcher_node(state: AgentState) -> AgentState:
    enriched = state.get("enriched_data") or {}
    homepage_text = enriched.get("homepage_text") or ""
    about_text = enriched.get("about_page_text") or ""

    if not homepage_text and not about_text:
        state["business_identity_summary"] = "Aucune donnée scrapée disponible pour ce prospect."
        return state

    user_prompt = (
        f"Nom de l'entreprise: {state.get('company_name')}\n"
        f"Secteur: {state.get('sector')} / {state.get('business_type')}\n"
        f"Texte page d'accueil: {homepage_text[:2000]}\n"
        f"Texte page 'A propos': {about_text[:2000]}"
    )

    try:
        result = call_llm_json(RESEARCHER_SYSTEM_PROMPT, user_prompt)
        state["business_identity_summary"] = result.get("business_identity_summary", "")
    except LLMError as e:
        state["error"] = f"Researcher: {str(e)}"
    return state


def strategist_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    user_prompt = (
        f"Résumé business du prospect: {state.get('business_identity_summary')}\n"
        f"Secteur: {state.get('sector')} / {state.get('business_type')}"
    )

    try:
        result = call_llm_json(STRATEGIST_SYSTEM_PROMPT, user_prompt)
        friction_points = result.get("friction_points", [])
        state["friction_points"] = friction_points

        # RAG: recherche les features Fastriom pertinentes pour chaque friction
        matched = []
        for friction in friction_points:
            hits = search_features(friction, k=2)
            matched.extend(hits)
        # Déduplique par source
        seen_sources = set()
        deduped = []
        for hit in matched:
            if hit["source"] not in seen_sources:
                deduped.append(hit)
                seen_sources.add(hit["source"])
        state["matched_features"] = deduped

    except LLMError as e:
        state["error"] = f"Strategist: {str(e)}"
    return state


def copywriter_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    features_text = "\n".join(
        f"- ({f['source']}): {f['content'][:300]}" for f in state.get("matched_features", [])
    )
    friction_text = "\n".join(f"- {f}" for f in state.get("friction_points", []))

    critique_feedback = state.get("critique_feedback")
    feedback_section = (
        f"\n\nRETOUR CRITIQUE A CORRIGER IMPÉRATIVEMENT: {critique_feedback}"
        if critique_feedback else ""
    )

    user_prompt = (
        f"Entreprise: {state.get('company_name')} ({state.get('city')}, {state.get('country')})\n"
        f"Nom du contact: {state.get('contact_full_name') or 'responsable de l établissement'}\n"
        f"Résumé business: {state.get('business_identity_summary')}\n"
        f"Points de friction identifiés:\n{friction_text}\n"
        f"Fonctionnalités Fastriom pertinentes:\n{features_text}"
        f"{feedback_section}"
    )

    try:
        result = call_llm_json(COPYWRITER_SYSTEM_PROMPT, user_prompt, temperature=0.6)
        state["email_subject"] = result.get("email_subject", "")
        state["email_body"] = result.get("email_body", "")
        state["framework_used"] = result.get("framework_used", "AIDA")
    except LLMError as e:
        state["error"] = f"Copywriter: {str(e)}"
    return state


def compliance_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    user_prompt = (
        f"Objet: {state.get('email_subject')}\n"
        f"Corps de l'email:\n{state.get('email_body')}"
    )

    try:
        result = call_llm_json(COMPLIANCE_SYSTEM_PROMPT, user_prompt, temperature=0.2)
        status = result.get("critique_status", "REJECTED").upper()
        state["critique_status"] = status if status in ("APPROVED", "REJECTED") else "REJECTED"
        state["critique_feedback"] = result.get("critique_feedback")

        # Historique pour audit / debug
        history = state.get("revision_history", [])
        history.append({
            "revision": state.get("revision_count", 0),
            "email_subject": state.get("email_subject"),
            "email_body": state.get("email_body"),
            "critique_status": state["critique_status"],
            "critique_feedback": state["critique_feedback"],
        })
        state["revision_history"] = history

    except LLMError as e:
        state["error"] = f"Compliance: {str(e)}"
    return state


def increment_revision_node(state: AgentState) -> AgentState:
    state["revision_count"] = state.get("revision_count", 0) + 1
    return state