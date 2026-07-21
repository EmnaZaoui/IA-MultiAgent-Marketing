import os
from flask import Blueprint, jsonify

from app.extensions import db
from app.models.lead import Lead, LeadStatus
from app.models.email_draft import EmailDraft
from app.agents.graph import marketing_agent_graph

agent_pipeline_bp = Blueprint("agent_pipeline", __name__)


@agent_pipeline_bp.post("/leads/<int:lead_id>/generate-email")
def generate_email(lead_id):
    lead = Lead.query.get(lead_id)
    if lead is None:
        return jsonify({"error": "Lead introuvable"}), 404

    if lead.status.value != "ENRICHED":
        return jsonify({
            "error": f"Le lead doit être au statut ENRICHED avant génération (statut actuel: {lead.status.value})"
        }), 409

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
        lead.status = LeadStatus.FAILED
        lead.error_message = f"Erreur pipeline agents: {str(e)}"
        db.session.commit()
        return jsonify({"error": str(e)}), 500

    if final_state.get("error"):
        lead.status = LeadStatus.FAILED
        lead.error_message = final_state["error"]
        db.session.commit()
        return jsonify({"lead_id": lead.id, "status": "FAILED", "error": final_state["error"]}), 200

    critique_status = final_state.get("critique_status")
    revision_count = final_state.get("revision_count", 0)
    max_retries = final_state.get("max_retries", 3)

    draft = EmailDraft(
        lead_id=lead.id,
        subject=final_state.get("email_subject"),
        body=final_state.get("email_body"),
        framework_used=final_state.get("framework_used"),
        matched_features=final_state.get("matched_features", []),
        friction_points=final_state.get("friction_points", []),
        critique_status=critique_status if critique_status == "APPROVED" else "MAX_RETRIES_EXCEEDED",
        critique_feedback=final_state.get("critique_feedback"),
        revision_count=revision_count,
        revision_history=final_state.get("revision_history", []),
    )
    db.session.add(draft)

    if critique_status == "APPROVED":
        lead.status = LeadStatus.DRAFTED
        lead.error_message = None
    else:
        lead.status = LeadStatus.FAILED
        lead.error_message = f"Email rejeté après {revision_count} révisions: {final_state.get('critique_feedback')}"

    db.session.commit()

    return jsonify({
        "lead_id": lead.id,
        "lead_status": lead.status.value,
        "draft": draft.to_dict(),
    }), 201


@agent_pipeline_bp.get("/leads/<int:lead_id>/email-drafts")
def list_drafts(lead_id):
    drafts = EmailDraft.query.filter_by(lead_id=lead_id).order_by(EmailDraft.created_at.desc()).all()
    return jsonify({"lead_id": lead_id, "drafts": [d.to_dict() for d in drafts]})