import sys
import time

sys.path.insert(0, ".")

from app import create_app
from app.extensions import db
from app.models.lead import Lead, LeadStatus
from app.agents.graph import marketing_agent_graph
import os

MAX_LEADS_TO_EVALUATE = 50


def run_evaluation():
    app = create_app()
    with app.app_context():
        leads = Lead.query.filter_by(status=LeadStatus.ENRICHED).limit(MAX_LEADS_TO_EVALUATE).all()

        if not leads:
            print("Aucun lead au statut ENRICHED trouvé. Enrichis d'abord des leads (Sprint 2).")
            return

        stats = {"total": 0, "approved": 0, "max_retries_exceeded": 0, "errors": 0}
        results = []

        for lead in leads:
            stats["total"] += 1
            print(f"\n[{stats['total']}/{len(leads)}] Traitement: {lead.company_name} ({lead.contact_email})")

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

            start = time.time()
            try:
                final_state = marketing_agent_graph.invoke(initial_state)
                elapsed = round(time.time() - start, 2)

                if final_state.get("error"):
                    stats["errors"] += 1
                    print(f"  -> ERREUR ({elapsed}s): {final_state['error']}")
                elif final_state.get("critique_status") == "APPROVED":
                    stats["approved"] += 1
                    print(f"  -> APPROUVÉ ({elapsed}s) après {final_state.get('revision_count', 0)} révision(s)")
                else:
                    stats["max_retries_exceeded"] += 1
                    print(f"  -> REJETÉ (max retries) ({elapsed}s): {final_state.get('critique_feedback')}")

                results.append({
                    "lead_id": lead.id,
                    "company": lead.company_name,
                    "outcome": final_state.get("critique_status", "ERROR"),
                    "revisions": final_state.get("revision_count", 0),
                    "elapsed_seconds": elapsed,
                })
            except Exception as e:
                stats["errors"] += 1
                print(f"  -> EXCEPTION NON GÉRÉE: {str(e)}")

        print("\n" + "=" * 50)
        print("RÉSUMÉ DE L'ÉVALUATION")
        print("=" * 50)
        for key, value in stats.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    run_evaluation()