from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db


class EmailDraft(db.Model):
    __tablename__ = "email_drafts"

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    subject = db.Column(db.String(255))
    body = db.Column(db.Text)
    framework_used = db.Column(db.String(10))
    matched_features = db.Column(JSONB, default=list)
    friction_points = db.Column(JSONB, default=list)
    critique_status = db.Column(db.String(20), nullable=False, default="PENDING")
    critique_feedback = db.Column(db.Text)
    revision_count = db.Column(db.Integer, default=0)
    revision_history = db.Column(JSONB, default=list)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "subject": self.subject,
            "body": self.body,
            "framework_used": self.framework_used,
            "matched_features": self.matched_features,
            "friction_points": self.friction_points,
            "critique_status": self.critique_status,
            "critique_feedback": self.critique_feedback,
            "revision_count": self.revision_count,
            "revision_history": self.revision_history,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }