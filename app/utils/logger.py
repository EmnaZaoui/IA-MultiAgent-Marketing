import logging
from logging.handlers import RotatingFileHandler


def setup_logger(app):
    handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=5)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)