from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db


class PipelineRun(db.Model):
    __tablename__ = "pipeline_runs"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default="RUNNING")
    triggered_by = db.Column(db.String(20), nullable=False, default="MANUAL")
    current_step = db.Column(db.String(30))
    stats = db.Column(JSONB, default=dict)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    finished_at = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "triggered_by": self.triggered_by,
            "current_step": self.current_step,
            "stats": self.stats,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }