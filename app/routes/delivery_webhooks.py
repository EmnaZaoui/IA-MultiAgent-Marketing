from flask import Blueprint, request, jsonify, current_app

from app.extensions import db
from app.models.email_send import EmailSend
from app.services.campaign_service import add_to_suppression

delivery_webhooks_bp = Blueprint("delivery_webhooks", __name__)


@delivery_webhooks_bp.post("/webhooks/bounce")
def handle_bounce():
    """Webhook générique pour recevoir une notification de bounce asynchrone
    (ex: retour différé du serveur SMTP relais, ou futur fournisseur tiers)."""
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    reason = data.get("reason", "Bounce non spécifié")

    if not email:
        return jsonify({"error": "Champ 'email' requis"}), 400

    email_send = (
        EmailSend.query.filter_by(recipient_email=email)
        .order_by(EmailSend.created_at.desc())
        .first()
    )

    if email_send:
        from datetime import datetime
        email_send.bounced_at = datetime.utcnow()
        email_send.delivery_status = "BOUNCED"
        db.session.commit()

    add_to_suppression(email, reason="BOUNCED")
    current_app.logger.info(f"Bounce enregistré pour {email}: {reason}")

    return jsonify({"message": "Bounce enregistré", "email": email}), 200