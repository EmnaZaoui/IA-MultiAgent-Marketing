import os
from flask import Flask
from config import Config
from app.extensions import db
from app.utils.logger import setup_logger


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    db.init_app(app)
    setup_logger(app)

    from app.routes.ingestion import ingestion_bp
    from app.routes.webhooks import webhooks_bp

    app.register_blueprint(ingestion_bp, url_prefix="/api/v1/leads")
    app.register_blueprint(webhooks_bp, url_prefix="/api/v1/webhooks")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "AI_MultiAgent_Marketing"}

    return app