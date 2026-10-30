from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").status_code == 200

def test_unknown():
    assert client.get("/api/v1/words/rogi").json()["status"] in ("valid", "unknown")
