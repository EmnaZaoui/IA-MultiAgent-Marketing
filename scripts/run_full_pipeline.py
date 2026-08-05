import sys
sys.path.insert(0, ".")

from app import create_app
from app.services.pipeline_orchestrator import _run_discovery_phase, _run_enrichment_phase, _run_email_generation_phase

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("=== ÉTAPE 1: Découverte de leads ===")
        discovery_stats = _run_discovery_phase()
        print(discovery_stats)

        print("\n=== ÉTAPE 2: Enrichissement ===")
        enrichment_stats = _run_enrichment_phase()
        print(enrichment_stats)

        print("\n=== ÉTAPE 3: Génération d'emails ===")
        email_stats = _run_email_generation_phase()
        print(email_stats)

        print("\n=== RÉSUMÉ COMPLET ===")
        print({"discovery": discovery_stats, "enrichment": enrichment_stats, "email_generation": email_stats})