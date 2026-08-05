import os
import json
import logging
import threading

from app.extensions import db
from app.models.lead import Lead, LeadStatus
from app.models.email_draft import EmailDraft
from app.models.pipeline_run import PipelineRun
from app.services.enrichment_service import enrich_lead
from app.services.lead_search_service import discover_leads
from app.agents.graph import marketing_agent_graph

logger = logging.getLogger(__name__)

SEARCH_TARGETS_PATH = "config/search_targets.json"


def _load_search_targets() -> dict:
    with open(SEARCH_TARGETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _run_discovery_phase() -> dict:
    """ÉTAPE 1: recherche automatique de nouveaux leads selon le profil ICP configuré."""
    config = _load_search_targets()
    targets = config.get("targets", [])
    max_results = config.get("max_results_per_target", 8)

    aggregated_stats = {"targets_processed": 0, "total_created": 0, "total_searched": 0}

    for target in targets:
        query = target["query"]
        hint = target.get("business_type_hint", "")
        logger.info(f"[DISCOVERY] Recherche: '{query}'")

        try:
            result = discover_leads(query, hint, max_results)
            stats = result.get("stats", {})
            aggregated_stats["total_created"] += stats.get("created", 0)
            aggregated_stats["total_searched"] += stats.get("searched", 0)
        except Exception as e:
            logger.error(f"[DISCOVERY] Échec sur la cible '{query}': {str(e)}")

        aggregated_stats["targets_processed"] += 1

    return aggregated_stats


def _run_enrichment_phase(limit: int = 200) -> dict:
    """ÉTAPE 2: enrichit tous les leads en attente (LEAD_IMPORTED)."""
    leads = Lead.query.filter_by(status=LeadStatus.LEAD_IMPORTED).limit(limit).all()
    stats = {"total": len(leads), "enriched": 0, "failed": 0}

    for lead in leads:
        try:
            result, _ = enrich_lead(lead.id)
            if result.get("status") == "ENRICHED":
                stats["enriched"] += 1
            else:
                stats["failed"] += 1
        except Exception as e:
            logger.error(f"[ENRICHMENT] Échec lead {lead.id}: {str(e)}")
            stats["failed"] += 1

        logger.info(f"[ENRICHMENT] Lead {lead.id} ({lead.company_name}): terminé")

    return stats


def _run_email_generation_phase(limit: int = 200) -> dict:
    """ÉTAPE 3: génère un email pour tous les leads enrichis (ENRICHED)."""
    leads = Lead.query.filter_by(status=LeadStatus.ENRICHED).limit(limit).all()
    stats = {"total": len(leads), "drafted": 0, "failed": 0}

    for lead in leads:
        initial_state = {
            "lead_id": lead.id,
            "company_name": lead.company_name,
            "website_url": lead.website_url,
            "sector": lead.sector,
            "business_type": lead.business_type,
            "city": lead.city,
            "country": lead.country,
            "enriched_data": lead.enriched_data or {},
            "revision_count": 0,
            "max_retries": int(os.getenv("LLM_MAX_RETRIES_CRITIQUE", 3)),
            "revision_history": [],
        }

        try:
            final_state = marketing_agent_graph.invoke(initial_state)
        except Exception as e:
            logger.error(f"[EMAIL_GEN] Exception lead {lead.id}: {str(e)}")
            lead.status = LeadStatus.FAILED
            lead.error_message = str(e)
            db.session.commit()
            stats["failed"] += 1
            continue

        if final_state.get("error"):
            lead.status = LeadStatus.FAILED
            lead.error_message = final_state["error"]
            db.session.commit()
            stats["failed"] += 1
            continue

        critique_status = final_state.get("critique_status")
        draft = EmailDraft(
            lead_id=lead.id,
            subject=final_state.get("email_subject"),
            body=final_state.get("email_body"),
            framework_used=final_state.get("framework_used"),
            matched_features=final_state.get("matched_features", []),
            friction_points=final_state.get("friction_points", []),
            critique_status=critique_status if critique_status == "APPROVED" else "MAX_RETRIES_EXCEEDED",
            critique_feedback=final_state.get("critique_feedback"),
            revision_count=final_state.get("revision_count", 0),
            revision_history=final_state.get("revision_history", []),
        )
        db.session.add(draft)

        if critique_status == "APPROVED":
            lead.status = LeadStatus.DRAFTED
            stats["drafted"] += 1
        else:
            lead.status = LeadStatus.FAILED
            lead.error_message = f"Rejeté après {final_state.get('revision_count', 0)} révisions"
            stats["failed"] += 1

        db.session.commit()
        logger.info(f"[EMAIL_GEN] Lead {lead.id}: {lead.status.value}")

    return stats


def _execute_full_pipeline(app, run_id: int):
    """
    Fonction exécutée dans un thread séparé (arrière-plan). Nécessite son
    propre app_context Flask car elle tourne hors du cycle requête/réponse.
    """
    with app.app_context():
        run = PipelineRun.query.get(run_id)
        try:
            run.current_step = "DISCOVERY"
            db.session.commit()
            discovery_stats = _run_discovery_phase()

            run.current_step = "ENRICHMENT"
            db.session.commit()
            enrichment_stats = _run_enrichment_phase()

            run.current_step = "EMAIL_GENERATION"
            db.session.commit()
            email_stats = _run_email_generation_phase()

            run.status = "COMPLETED"
            run.current_step = "DONE"
            run.stats = {
                "discovery": discovery_stats,
                "enrichment": enrichment_stats,
                "email_generation": email_stats,
            }

        except Exception as e:
            logger.exception(f"[PIPELINE RUN {run_id}] Échec global")
            run.status = "FAILED"
            run.error_message = str(e)

        finally:
            from datetime import datetime
            run.finished_at = datetime.utcnow()
            db.session.commit()


def start_full_pipeline_async(app, triggered_by: str = "MANUAL") -> PipelineRun:
    """
    Point d'entrée principal: crée un enregistrement PipelineRun, lance le
    traitement complet (discovery -> enrichment -> email generation) dans un
    thread d'arrière-plan, et retourne IMMÉDIATEMENT l'objet run (status=RUNNING).
    """
    run = PipelineRun(status="RUNNING", triggered_by=triggered_by, current_step="STARTING")
    db.session.add(run)
    db.session.commit()

    thread = threading.Thread(target=_execute_full_pipeline, args=(app, run.id), daemon=True)
    thread.start()

    return run