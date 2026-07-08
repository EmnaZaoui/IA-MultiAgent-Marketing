from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db


class CsvImportBatch(db.Model):
    __tablename__ = "csv_import_batches"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    total_rows = db.Column(db.Integer, default=0)
    imported_rows = db.Column(db.Integer, default=0)
    duplicate_rows = db.Column(db.Integer, default=0)
    failed_rows = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="PROCESSING")
    error_details = db.Column(JSONB, default=list)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    finished_at = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "total_rows": self.total_rows,
            "imported_rows": self.imported_rows,
            "duplicate_rows": self.duplicate_rows,
            "failed_rows": self.failed_rows,
            "status": self.status,
            "error_details": self.error_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class WebhookEvent(db.Model):
    __tablename__ = "webhook_events"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    payload = db.Column(JSONB, nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id", ondelete="SET NULL"))
    processed = db.Column(db.Boolean, default=False)
    received_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)