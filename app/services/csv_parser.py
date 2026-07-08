import csv
import io
from datetime import datetime

from app.extensions import db
from app.models.tracking import CsvImportBatch
from app.services.lead_service import (
    build_lead_payload,
    validate_lead_payload,
    email_already_exists,
    create_lead,
)

REQUIRED_COLUMNS = {"company_name", "contact_email", "sector"}


def parse_and_import_csv(file_stream, filename: str) -> dict:
    """
    Parse un fichier CSV uploadé et importe les leads valides en base.
    Retourne un résumé détaillé (utile pour affichage / debug / Sprint 3 QA).
    """
    batch = CsvImportBatch(filename=filename, status="PROCESSING")
    db.session.add(batch)
    db.session.flush()  

    content = file_stream.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
        batch.status = "FAILED"
        batch.error_details = [
            {"error": f"Colonnes requises manquantes: {REQUIRED_COLUMNS}", "found": reader.fieldnames}
        ]
        batch.finished_at = datetime.utcnow()
        db.session.commit()
        return batch.to_dict()

    total_rows = 0
    imported_rows = 0
    duplicate_rows = 0
    failed_rows = 0
    errors = []

    for line_number, row in enumerate(reader, start=2):  # ligne 1 = en-têtes
        total_rows += 1
        payload = build_lead_payload(row, source="CSV_IMPORT")

        is_valid, error_message = validate_lead_payload(payload)
        if not is_valid:
            failed_rows += 1
            errors.append({"line": line_number, "email": payload.get("contact_email"), "reason": error_message})
            continue

        if email_already_exists(payload["contact_email"]):
            duplicate_rows += 1
            errors.append({"line": line_number, "email": payload["contact_email"], "reason": "Email déjà existant"})
            continue

        create_lead(payload)
        imported_rows += 1

    batch.total_rows = total_rows
    batch.imported_rows = imported_rows
    batch.duplicate_rows = duplicate_rows
    batch.failed_rows = failed_rows
    batch.error_details = errors
    batch.status = "COMPLETED"
    batch.finished_at = datetime.utcnow()

    db.session.commit()
    return batch.to_dict()