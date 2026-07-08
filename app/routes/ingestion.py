from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.models.lead import Lead
from app.services.csv_parser import parse_and_import_csv
from app.utils.validators import allowed_file

ingestion_bp = Blueprint("ingestion", __name__)


@ingestion_bp.post("/import-csv")
def import_csv():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni (champ 'file' attendu)"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400

    if not allowed_file(file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
        return jsonify({"error": "Extension non autorisée, seul le .csv est accepté"}), 400

    filename = secure_filename(file.filename)

    try:
        summary = parse_and_import_csv(file.stream, filename)
        current_app.logger.info(f"Import CSV '{filename}' terminé: {summary}")
        return jsonify(summary), 201
    except Exception as e:
        current_app.logger.exception(f"Erreur lors de l'import CSV '{filename}'")
        return jsonify({"error": f"Erreur interne lors du parsing: {str(e)}"}), 500


@ingestion_bp.route("/", methods=["GET"]) 
def list_leads():
    status = request.args.get("status")
    sector = request.args.get("sector")
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    query = Lead.query
    if status:
        query = query.filter(Lead.status == status.upper())
    if sector:
        query = query.filter(Lead.sector == sector.upper())

    pagination = query.order_by(Lead.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "leads": [lead.to_dict() for lead in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    })


@ingestion_bp.get("/<int:lead_id>")
def get_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    return jsonify(lead.to_dict())