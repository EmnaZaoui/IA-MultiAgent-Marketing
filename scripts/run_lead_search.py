import sys
sys.path.insert(0, ".")

from app import create_app
from app.services.lead_search_service import discover_leads

# Modifie ces requêtes selon les cibles de prospection du moment
SEARCH_QUERIES = [
    {"query": "restaurants Tunis", "business_type_hint": "restaurant"},
    {"query": "boutique vetements Paris", "business_type_hint": "boutique_vetements"},
    {"query": "boulangerie artisanale Lyon", "business_type_hint": "boulangerie"},
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for job in SEARCH_QUERIES:
            print(f"\n=== Recherche: {job['query']} ===")
            result = discover_leads(job["query"], job["business_type_hint"], max_results=10)
            print(f"Stats: {result['stats']}")
            print(f"Exports: {result['exports']}")