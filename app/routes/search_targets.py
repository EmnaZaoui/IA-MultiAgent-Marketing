from flask import Blueprint, jsonify, request

from app.services.search_targets_config_service import (
    get_config,
    add_target,
    update_target,
    delete_target,
    update_max_results,
    SearchTargetsConfigError,
)

search_targets_bp = Blueprint("search_targets", __name__)


@search_targets_bp.get("/config/search-targets")
def list_search_targets():
    """Liste toutes les cibles de recherche configurées pour la découverte de leads."""
    config = get_config()
    return jsonify(config), 200


@search_targets_bp.post("/config/search-targets")
def create_search_target():
    """Ajoute une nouvelle cible de recherche."""
    body = request.get_json(silent=True) or {}
    try:
        new_target = add_target(body.get("query"), body.get("business_type_hint", ""))
        return jsonify(new_target), 201
    except SearchTargetsConfigError as e:
        return jsonify({"error": str(e)}), 400


@search_targets_bp.put("/config/search-targets/<target_id>")
def edit_search_target(target_id):
    """Modifie une cible de recherche existante."""
    body = request.get_json(silent=True) or {}
    try:
        updated = update_target(target_id, body.get("query"), body.get("business_type_hint", ""))
        return jsonify(updated), 200
    except SearchTargetsConfigError as e:
        return jsonify({"error": str(e)}), 400


@search_targets_bp.delete("/config/search-targets/<target_id>")
def remove_search_target(target_id):
    """Supprime une cible de recherche."""
    try:
        delete_target(target_id)
        return jsonify({"message": "Cible supprimée avec succès."}), 200
    except SearchTargetsConfigError as e:
        return jsonify({"error": str(e)}), 404


@search_targets_bp.put("/config/search-targets/settings")
def update_search_settings():
    """Met à jour le nombre maximum de résultats à traiter par cible."""
    body = request.get_json(silent=True) or {}
    try:
        config = update_max_results(int(body.get("max_results_per_target", 8)))
        return jsonify(config), 200
    except (SearchTargetsConfigError, ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400