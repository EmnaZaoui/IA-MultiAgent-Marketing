import enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import ENUM as PGEnum, JSONB
from app.extensions import db


class LeadStatus(enum.Enum):
    LEAD_IMPORTED = "LEAD_IMPORTED"
    ENRICHED = "ENRICHED"
    DRAFTED = "DRAFTED"
    SENT = "SENT"
    FAILED = "FAILED"


lead_status_pg_enum = PGEnum(
    LeadStatus,
    name="lead_status",
    create_type=False,  
    values_callable=lambda enum_cls: [e.value for e in enum_cls],
)


class Lead(db.Model):
    __tablename__ = "leads"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    contact_full_name = db.Column(db.String(255))
    contact_email = db.Column(db.String(255), nullable=False, unique=True)
    contact_phone = db.Column(db.String(50))
    website_url = db.Column(db.String(500))
    sector = db.Column(db.String(50), nullable=False)
    business_type = db.Column(db.String(100))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    source = db.Column(db.String(50), nullable=False, default="CSV_IMPORT")
    status = db.Column(lead_status_pg_enum, nullable=False, default=LeadStatus.LEAD_IMPORTED)
    enriched_data = db.Column(JSONB, default=dict)
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "contact_full_name": self.contact_full_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "website_url": self.website_url,
            "sector": self.sector,
            "business_type": self.business_type,
            "city": self.city,
            "country": self.country,
            "source": self.source,
            "status": self.status.value if isinstance(self.status, LeadStatus) else self.status,
            "enriched_data": self.enriched_data,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }