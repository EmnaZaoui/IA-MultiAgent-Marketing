import os
import random
import time
import logging
import threading

from app.extensions import db
from app.models.lead import Lead, LeadStatus
from app.models.email_draft import EmailDraft
from app.models.email_send import EmailSend
from app.models.suppression import SuppressionEntry, CampaignRun
from app.services.smtp_service import send_email, SMTPError
from app.services.tracking_service import generate_tracking_token, wrap_email_with_tracking

logger = logging.getLogger(__name__)


def _get_domain(email: str) -> str:
    return email.split("@")[-1].lower() if "@" in email else ""


def is_suppressed(email: str) -> bool:
    """Vérifie si l'email (ou son domaine) est dans la liste de suppression.
    Conforme au cahier des charges: 'immediately excluding that entity domain
    from any future iteration'."""
    domain = _get_domain(email)
    exists = SuppressionEntry.query.filter(
        (SuppressionEntry.email == email) | (SuppressionEntry.domain == domain)
    ).first()
    return exists is not None


def add_to_suppression(email: str, reason: str) -> None:
    if is_suppressed(email):
        return
    entry = SuppressionEntry(email=email, domain=_get_domain(email), reason=reason)
    db.session.add(entry)
    db.session.commit()
    logger.info(f"Ajouté à la liste de suppression: {email} (raison: {reason})")


def _get_qualified_leads_for_sending(limit: int):
    """Sélectionne les leads prêts à recevoir un email:
    statut DRAFTED + dernier draft APPROVED + pas dans la suppression list."""
    leads = Lead.query.filter_by(status=LeadStatus.DRAFTED).limit(limit * 2).all()  # marge pour filtrage
    qualified = []

    for lead in leads:
        if is_suppressed(lead.contact_email):
            continue

        draft = (
            EmailDraft.query.filter_by(lead_id=lead.id, critique_status="APPROVED")
            .order_by(EmailDraft.created_at.desc())
            .first()
        )
        if draft:
            qualified.append((lead, draft))

        if len(qualified) >= limit:
            break

    return qualified


def _send_single_email(lead: Lead, draft: EmailDraft) -> EmailSend:
    token = generate_tracking_token()
    email_send = EmailSend(
        lead_id=lead.id,
        draft_id=draft.id,
        tracking_token=token,
        recipient_email=lead.contact_email,
        subject=draft.subject,
        send_status="PENDING",
    )
    db.session.add(email_send)
    db.session.commit()

    if is_suppressed(lead.contact_email):
        email_send.send_status = "SUPPRESSED"
        db.session.commit()
        return email_send

    html_body = wrap_email_with_tracking(draft.body, token)

    try:
        send_email(lead.contact_email, draft.subject, html_body, draft.body)
        mode = os.getenv("EMAIL_SEND_MODE", "dry_run").lower()
        email_send.send_status = "SENT" if mode != "dry_run" else "SIMULATED"
        from datetime import datetime
        email_send.sent_at = datetime.utcnow()
        lead.status = LeadStatus.SENT
        lead.error_message = None

    except SMTPError as e:
        email_send.send_status = "FAILED"
        email_send.error_message = str(e)
        lead.status = LeadStatus.FAILED
        lead.error_message = f"Échec envoi SMTP: {str(e)}"

    db.session.commit()
    return email_send


def _execute_batch_send(app, run_id: int, batch_size: int):
    """Exécuté en thread d'arrière-plan: envoie les emails un par un avec
    délai aléatoire entre chaque envoi (protection réputation domaine)."""
    with app.app_context():
        run = CampaignRun.query.get(run_id)
        delay_min = int(os.getenv("DELIVERY_DELAY_MIN_SECONDS", 120))
        delay_max = int(os.getenv("DELIVERY_DELAY_MAX_SECONDS", 420))

        try:
            qualified = _get_qualified_leads_for_sending(batch_size)
            run.total_targeted = len(qualified)
            db.session.commit()

            for index, (lead, draft) in enumerate(qualified, start=1):
                logger.info(f"[CAMPAIGN {run_id}] Envoi {index}/{len(qualified)}: {lead.contact_email}")

                email_send = _send_single_email(lead, draft)

                if email_send.send_status == "SENT":
                    run.total_sent += 1
                elif email_send.send_status == "SUPPRESSED":
                    run.total_suppressed += 1
                else:
                    run.total_failed += 1

                db.session.commit()

                # Délai aléatoire de protection de réputation (sauf après le dernier envoi)
                if index < len(qualified):
                    delay = random.randint(delay_min, delay_max)
                    logger.info(f"[CAMPAIGN {run_id}] Attente de {delay}s avant le prochain envoi...")
                    time.sleep(delay)

            run.status = "COMPLETED"

        except Exception as e:
            logger.exception(f"[CAMPAIGN {run_id}] Échec global")
            run.status = "FAILED"

        finally:
            from datetime import datetime
            run.finished_at = datetime.utcnow()
            db.session.commit()


def is_campaign_already_running() -> bool:
    active = CampaignRun.query.filter_by(status="RUNNING").first()
    return active is not None

def start_batch_send_async(app, batch_size: int = 100) -> CampaignRun:
    if is_campaign_already_running():
        raise RuntimeError("Une campagne d'envoi est déjà en cours. Attendez sa fin avant d'en lancer une nouvelle.")

    run = CampaignRun(status="RUNNING")
    db.session.add(run)
    db.session.commit()

    thread = threading.Thread(target=_execute_batch_send, args=(app, run.id, batch_size), daemon=True)
    thread.start()

    return run