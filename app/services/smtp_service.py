import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class SMTPError(Exception):
    pass


def _resolve_recipient(original_to_email: str) -> tuple[str, bool]:
    """
    Détermine le vrai destinataire selon le mode d'envoi configuré.
    Retourne (email_effectif, was_redirected).
    """
    mode = os.getenv("EMAIL_SEND_MODE", "dry_run").lower()

    if mode == "sandbox":
        redirect_email = os.getenv("DRY_RUN_REDIRECT_EMAIL")
        if not redirect_email:
            raise SMTPError("EMAIL_SEND_MODE=sandbox nécessite DRY_RUN_REDIRECT_EMAIL dans .env")
        return redirect_email, True

    return original_to_email, False


def send_email(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    """
    Envoie un email via SMTP sécurisé (TLS), en respectant EMAIL_SEND_MODE:
    - dry_run: ne rien envoyer, juste logger (mode par défaut, le plus sûr)
    - sandbox: envoyer réellement mais uniquement vers DRY_RUN_REDIRECT_EMAIL
    - production: envoi réel vers le vrai destinataire
    """
    mode = os.getenv("EMAIL_SEND_MODE", "dry_run").lower()

    if mode == "dry_run":
        logger.info(
            f"[DRY_RUN] Email NON envoyé (simulation). "
            f"Destinataire prévu: {to_email} | Sujet: {subject}"
        )
        return  # On s'arrête ici, aucun appel SMTP réel

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", 587))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_name = os.getenv("SMTP_FROM_NAME", "Fastriom")
    from_email = os.getenv("SMTP_FROM_EMAIL", username)

    if not all([host, username, password]):
        raise SMTPError("Configuration SMTP incomplète dans .env (SMTP_HOST/USERNAME/PASSWORD)")

    actual_recipient, was_redirected = _resolve_recipient(to_email)

    final_subject = subject
    final_html = html_body
    if was_redirected:
        final_subject = f"[SANDBOX → destinataire réel: {to_email}] {subject}"
        final_html = (
            f'<div style="background:#fff3cd;padding:12px;margin-bottom:16px;'
            f'border:1px solid #ffc107;font-family:sans-serif;font-size:13px;">'
            f'⚠️ MODE SANDBOX — Cet email était destiné à <strong>{to_email}</strong> '
            f'mais a été redirigé vers votre adresse de test.</div>{html_body}'
        )

    message = MIMEMultipart("alternative")
    message["Subject"] = final_subject
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = actual_recipient

    message.attach(MIMEText(text_body, "plain", "utf-8"))
    message.attach(MIMEText(final_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_email, actual_recipient, message.as_string())

        log_suffix = f" (redirigé depuis {to_email})" if was_redirected else ""
        logger.info(f"Email envoyé avec succès à {actual_recipient}{log_suffix}")

    except smtplib.SMTPRecipientsRefused as e:
        raise SMTPError(f"Destinataire refusé (probable bounce immédiat): {str(e)}")
    except smtplib.SMTPException as e:
        raise SMTPError(f"Erreur SMTP: {str(e)}")
    except Exception as e:
        raise SMTPError(f"Erreur inattendue lors de l'envoi: {str(e)}")