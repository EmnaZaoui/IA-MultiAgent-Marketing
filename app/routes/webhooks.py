from flask import Blueprint, request, jsonify, current_app

from app.extensions import db
from app.models.tracking import WebhookEvent
from app.services.lead_service import build_lead_payload, validate_lead_payload, email_already_exists, create_lead

webhooks_bp = Blueprint("webhooks", __name__)


@webhooks_bp.post("/lead-intake")
def lead_intake_webhook():
    token = request.headers.get("X-Webhook-Token")
    if token != current_app.config["WEBHOOK_SECRET_TOKEN"]:
        return jsonify({"error": "Token webhook invalide"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Corps JSON invalide ou manquant"}), 400

    event = WebhookEvent(event_type="LEAD_INTAKE", payload=data, processed=False)
    db.session.add(event)
    db.session.flush()

    payload = build_lead_payload(data, source="WEBHOOK")
    is_valid, error_message = validate_lead_payload(payload)

    if not is_valid:
        event.processed = True
        db.session.commit()
        return jsonify({"error": error_message, "event_id": event.id}), 422

    if email_already_exists(payload["contact_email"]):
        event.processed = True
        db.session.commit()
        return jsonify({"error": "Lead déjà existant", "event_id": event.id}), 409

    lead = create_lead(payload)
    event.processed = True
    db.session.commit()

    current_app.logger.info(f"Lead créé via webhook: {lead.contact_email}")
    return jsonify({"message": "Lead créé", "lead_id": lead.id, "event_id": event.id}), 201