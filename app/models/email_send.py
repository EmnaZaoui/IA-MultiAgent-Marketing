from datetime import datetime
from app.extensions import db


class EmailSend(db.Model):
    __tablename__ = "email_sends"

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    draft_id = db.Column(db.Integer, db.ForeignKey("email_drafts.id", ondelete="SET NULL"))
    tracking_token = db.Column(db.String(64), nullable=False, unique=True)
    recipient_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255))
    send_status = db.Column(db.String(20), nullable=False, default="PENDING")
    delivery_status = db.Column(db.String(20), nullable=False, default="UNKNOWN")
    error_message = db.Column(db.Text)
    opened_at = db.Column(db.DateTime(timezone=True))
    clicked_at = db.Column(db.DateTime(timezone=True))
    bounced_at = db.Column(db.DateTime(timezone=True))
    unsubscribed_at = db.Column(db.DateTime(timezone=True))
    sent_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "draft_id": self.draft_id,
            "recipient_email": self.recipient_email,
            "subject": self.subject,
            "send_status": self.send_status,
            "delivery_status": self.delivery_status,
            "error_message": self.error_message,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "bounced_at": self.bounced_at.isoformat() if self.bounced_at else None,
            "unsubscribed_at": self.unsubscribed_at.isoformat() if self.unsubscribed_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }