import io
import json
import pytest
from app import app, init_db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    yield

@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c

def login(client, username, password):
    resp = client.post("/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.get_json()
    csrf_token = resp.get_json().get("csrf_token")
    return csrf_token  

def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"

def test_login_logout_cycle(client):
    r = client.post("/login", json={"username": "user", "password": "user123"})
    assert r.status_code == 200
    r = client.get("/logout")
    assert r.status_code == 200

def test_predict_requires_auth(client):
    r = client.post("/predict", json={"sales": [1,2,3,4,5,6]})
    assert r.status_code in (302, 401)

def test_predict_validation_and_success(client):
    csrf_token = login(client, "user", "user123")

    r = client.post("/predict",
                    json={"sales": [10, 12, 11, 13, 12]},
                    headers={"X-CSRF-Token": csrf_token})
    assert r.status_code == 400

    sales = [i + (i % 3) for i in range(30)]
    r = client.post("/predict",
                    json={"sales": sales},
                    headers={"X-CSRF-Token": csrf_token})
    assert r.status_code == 200
    data = r.get_json()

    assert "predictions" in data
    assert isinstance(data["predictions"], list)
    assert len(data["predictions"]) >= 1
    for k in ("mae", "mse", "r2"):
        assert k in data and isinstance(data[k], (int, float))


def test_detect_anomaly_json(client):
    csrf_token = login(client, "user", "user123")
    vals = [10, 11, 12, 1000, 13, 14, -999]
    r = client.post("/detect_anomaly",
                    json={"sales": vals},
                    headers={"X-CSRF-Token": csrf_token})
    assert r.status_code == 200
    data = r.get_json()
    assert "indices" in data and "values" in data

def test_detect_anomaly_upload_csv(client):
    csrf_token = login(client, "user", "user123")
    csv_content = "sales\n1\n2\n3\n100\n5\n"
    data = {
        "file": (io.BytesIO(csv_content.encode("utf-8")), "series.csv"),
        "method": "zscore"
    }
    r = client.post("/detect_anomaly_upload",
                    data=data,
                    content_type="multipart/form-data",
                    headers={"X-CSRF-Token": csrf_token})
    assert r.status_code == 200
    payload = r.get_json()
    assert "indices" in payload and "values" in payload

def test_history_admin_only(client):
    # user login
    csrf_token = login(client, "user", "user123")
    r1 = client.get("/forecast_history")
    r2 = client.get("/anomaly_history")
    assert r1.status_code == 403
    assert r2.status_code == 403

    # Admin login
    csrf_token = login(client, "admin", "admin123")
    r1 = client.get("/forecast_history?limit=5&offset=0")
    r2 = client.get("/anomaly_history?limit=5&offset=0")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert "items" in r1.get_json()
    assert "items" in r2.get_json()
