import io
import pytest
from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_import_csv_missing_columns(client):
    csv_content = "company_name,contact_email\nAcme,test@test.com\n"
    data = {"file": (io.BytesIO(csv_content.encode()), "test.csv")}
    response = client.post("/api/v1/leads/import-csv", data=data, content_type="multipart/form-data")
    assert response.status_code == 201
    assert response.get_json()["status"] == "FAILED"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"