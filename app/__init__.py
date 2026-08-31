import os
from flask import Flask
from config import Config
from app.extensions import db
from app.utils.logger import setup_logger

from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint  


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    db.init_app(app)
    setup_logger(app)

    # CORS pour Angular
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:4200"]}})

    
    SWAGGER_URL = "/api/docs"
    OPENAPI_SPEC_URL = "/static/openapi.json"
    swaggerui_bp = get_swaggerui_blueprint(
        SWAGGER_URL, OPENAPI_SPEC_URL, config={"app_name": "AI Multi-Agent Marketing — Fastriom"}
    )
    app.register_blueprint(swaggerui_bp, url_prefix=SWAGGER_URL)

    # Importer les blueprints
    from app.routes.ingestion import ingestion_bp
    from app.routes.webhooks import webhooks_bp
    from app.routes.enrichment import enrichment_bp 
    from app.routes.agent_pipeline import agent_pipeline_bp
    from app.routes.lead_search import lead_search_bp
    from app.routes.tracking import tracking_bp
    from app.routes.delivery_webhooks import delivery_webhooks_bp
    from app.routes.campaigns import campaigns_bp

    # Enregistrer les blueprints
    app.register_blueprint(ingestion_bp, url_prefix="/api/v1/leads")
    app.register_blueprint(webhooks_bp, url_prefix="/api/v1/webhooks")
    app.register_blueprint(enrichment_bp, url_prefix="/api/v1")  
    app.register_blueprint(agent_pipeline_bp, url_prefix="/api/v1")
    app.register_blueprint(lead_search_bp, url_prefix="/api/v1")
    app.register_blueprint(tracking_bp, url_prefix="/api/v1")
    app.register_blueprint(delivery_webhooks_bp, url_prefix="/api/v1")
    app.register_blueprint(campaigns_bp, url_prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "AI_MultiAgent_Marketing"}

    return app