from datetime import datetime
from app.extensions import db


class SuppressionEntry(db.Model):
    __tablename__ = "suppression_list"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    domain = db.Column(db.String(255), nullable=False)
    reason = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "domain": self.domain,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CampaignRun(db.Model):
    __tablename__ = "campaign_runs"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default="RUNNING")
    total_targeted = db.Column(db.Integer, default=0)
    total_sent = db.Column(db.Integer, default=0)
    total_suppressed = db.Column(db.Integer, default=0)
    total_failed = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    finished_at = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "total_targeted": self.total_targeted,
            "total_sent": self.total_sent,
            "total_suppressed": self.total_suppressed,
            "total_failed": self.total_failed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }