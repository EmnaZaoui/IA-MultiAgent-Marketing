from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    # Entrée
    lead_id: int
    company_name: str
    website_url: str
    sector: str
    business_type: str
    city: str
    country: str
    enriched_data: dict  # scraped par le Sprint 2 (homepage_text, about_page_text, ...)

    # Sortie du Researcher
    business_identity_summary: str

    # Sortie du Strategist
    friction_points: list
    matched_features: list  # résultats de search_features (RAG)

    # Sortie du Copywriter
    email_subject: str
    email_body: str
    framework_used: str  # AIDA ou PAS

    # Sortie du Compliance Officer
    critique_status: str  # APPROVED | REJECTED
    critique_feedback: Optional[str]

    # Contrôle de la boucle
    revision_count: int
    max_retries: int
    revision_history: list

    # Erreurs
    error: Optional[str]
    final_status: str  # DRAFTED | FAILED