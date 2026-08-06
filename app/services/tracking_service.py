import os
import re
import secrets

TRACKING_PIXEL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
    "53de0000000c4944415408d763f8ffff3f0005fe02fea1e6a7c40000000049454e44ae426082"
)

URL_REGEX = re.compile(r'href=["\']([^"\']+)["\']')


def generate_tracking_token() -> str:
    """Génère un token unique, cryptographiquement sûr, pour identifier un envoi."""
    return secrets.token_urlsafe(24)


def wrap_email_with_tracking(html_body: str, token: str) -> str:
    """
    Injecte dans le HTML de l'email:
    - un pixel invisible de tracking d'ouverture
    - un lien de désabonnement en pied de page
    Les liens sortants restent inchangés ici (le tracking de clic se fait au
    niveau du contenu déjà généré par le Copywriter, qui n'inclut pas de
    liens externes — voir note ci-dessous).
    """
    base_url = os.getenv("BASE_TRACKING_URL", "http://localhost:5000")

    tracking_pixel = f'<img src="{base_url}/api/v1/track/open/{token}.png" width="1" height="1" style="display:none;" alt="" />'
    unsubscribe_link = (
        f'<p style="font-size:11px;color:#888;margin-top:24px;">'
        f'Cet email vous a été envoyé dans le cadre d\'une prospection B2B. '
        f'<a href="{base_url}/api/v1/track/unsubscribe/{token}">Se désinscrire</a>'
        f'</p>'
    )

    html_with_paragraphs = "".join(f"<p>{line}</p>" for line in html_body.split("\n") if line.strip())

    return f"<html><body>{html_with_paragraphs}{unsubscribe_link}{tracking_pixel}</body></html>"