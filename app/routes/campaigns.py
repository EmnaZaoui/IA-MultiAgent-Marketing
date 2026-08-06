from flask import Blueprint, jsonify, request, current_app

from app.models.suppression import CampaignRun
from app.models.email_send import EmailSend
from app.services.campaign_service import start_batch_send_async

campaigns_bp = Blueprint("campaigns", __name__)


@campaigns_bp.post("/campaigns/send-batch")
def send_batch():
    body = request.get_json(silent=True) or {}
    batch_size = min(int(body.get("batch_size", 100)), 100)  # plafond cahier des charges

    app = current_app._get_current_object()
    run = start_batch_send_async(app, batch_size)

    return jsonify({
        "message": f"Campagne d'envoi lancée en arrière-plan (jusqu'à {batch_size} prospects, délais 2-7min entre chaque envoi).",
        "campaign_run": run.to_dict(),
    }), 202


@campaigns_bp.get("/campaigns/<int:run_id>")
def get_campaign(run_id):
    run = CampaignRun.query.get(run_id)
    if run is None:
        return jsonify({"error": "Campagne introuvable"}), 404
    return jsonify(run.to_dict())


@campaigns_bp.get("/leads/<int:lead_id>/email-sends")
def list_email_sends(lead_id):
    sends = EmailSend.query.filter_by(lead_id=lead_id).order_by(EmailSend.created_at.desc()).all()
    return jsonify({"lead_id": lead_id, "sends": [s.to_dict() for s in sends]})