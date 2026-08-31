from flask import Blueprint, request, jsonify
from app.services.lead_search_service import discover_leads

lead_search_bp = Blueprint("lead_search", __name__)


@lead_search_bp.post("/leads/discover")
def discover():
    body = request.get_json(silent=True) or {}
    query = body.get("query")
    business_type_hint = body.get("business_type_hint", "")
    max_results = min(int(body.get("max_results", 10)), 50) 

    if not query:
        return jsonify({"error": "Champ 'query' requis, ex: 'restaurants Tunis'"}), 400

    result = discover_leads(query, business_type_hint, max_results)
    return jsonify(result), 200

