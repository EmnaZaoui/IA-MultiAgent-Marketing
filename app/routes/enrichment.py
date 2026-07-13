from flask import Blueprint, jsonify, request
from app.services.enrichment_service import enrich_lead
from app.services.vectorstore_service import search_features

enrichment_bp = Blueprint("enrichment", __name__)


@enrichment_bp.post("/leads/<int:lead_id>/enrich")
def enrich(lead_id):
    body, status_code = enrich_lead(lead_id)
    return jsonify(body), status_code


@enrichment_bp.get("/knowledge-base/search")
def kb_search():
    query = request.args.get("q")
    k = request.args.get("k", 3, type=int)
    if not query:
        return jsonify({"error": "Paramètre 'q' requis, ex: ?q=temps+attente+client"}), 400
    results = search_features(query, k=k)
    return jsonify({"query": query, "results": results})