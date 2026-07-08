from email_validator import validate_email, EmailNotValidError

ALLOWED_SECTORS = {"CHR", "RETAIL", "OTHER"}


def is_valid_email(email: str) -> tuple[bool, str]:
    if not email:
        return False, "Email manquant"
    try:
        validate_email(email, check_deliverability=False)
        return True, ""
    except EmailNotValidError as e:
        return False, str(e)


def is_valid_sector(sector: str) -> tuple[bool, str]:
    if not sector:
        return False, "Secteur manquant"
    if sector.upper() not in ALLOWED_SECTORS:
        return False, f"Secteur invalide: {sector} (attendu: {ALLOWED_SECTORS})"
    return True, ""


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def is_consumer_email_domain(email: str) -> bool:
    """Filtre B2C mentionné dans le cahier des charges (Sprint 2), préparé ici."""
    consumer_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"}
    domain = email.split("@")[-1].lower() if "@" in email else ""
    return domain in consumer_domains