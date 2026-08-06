from datetime import datetime
from flask import Blueprint, Response, redirect, current_app

from app.extensions import db
from app.models.email_send import EmailSend
from app.services.tracking_service import TRACKING_PIXEL_PNG
from app.services.campaign_service import add_to_suppression

tracking_bp = Blueprint("tracking", __name__)


@tracking_bp.get("/track/open/<token>.png")
def track_open(token):
    email_send = EmailSend.query.filter_by(tracking_token=token).first()
    if email_send and email_send.opened_at is None:
        email_send.opened_at = datetime.utcnow()
        email_send.delivery_status = "OPENED"
        db.session.commit()
        current_app.logger.info(f"Email ouvert: {email_send.recipient_email}")

    return Response(TRACKING_PIXEL_PNG, mimetype="image/png")


@tracking_bp.get("/track/click/<token>")
def track_click(token):
    """Prêt à l'usage dès qu'un lien cliquable sera ajouté dans le corps des
    emails générés (voir note dans tracking_service.py)."""
    email_send = EmailSend.query.filter_by(tracking_token=token).first()
    destination = "https://fastriom.com"  # URL de destination par défaut

    if email_send:
        if email_send.clicked_at is None:
            email_send.clicked_at = datetime.utcnow()
        email_send.delivery_status = "CLICKED"
        db.session.commit()
        current_app.logger.info(f"Clic enregistré: {email_send.recipient_email}")

    return redirect(destination, code=302)


@tracking_bp.get("/track/unsubscribe/<token>")
def track_unsubscribe(token):
    email_send = EmailSend.query.filter_by(tracking_token=token).first()

    if email_send:
        email_send.unsubscribed_at = datetime.utcnow()
        email_send.delivery_status = "UNSUBSCRIBED"
        db.session.commit()
        add_to_suppression(email_send.recipient_email, reason="UNSUBSCRIBED")
        current_app.logger.info(f"Désabonnement: {email_send.recipient_email}")

    return (
        "<html><body style='font-family:sans-serif;text-align:center;padding:60px;'>"
        "<h2>Vous avez été désabonné avec succès.</h2>"
        "<p>Vous ne recevrez plus d'emails de notre part.</p>"
        "</body></html>"
    ), 200