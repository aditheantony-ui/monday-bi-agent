from fastapi.testclient import TestClient

import main


def test_health():
    response = TestClient(main.app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_question_validation():
    response = TestClient(main.app).post("/agent/query", json={"question": ""})
    assert response.status_code == 422


def test_prediction_validation():
    response = TestClient(main.app).post(
        "/predictions",
        json={
            "deal_value": 100,
            "days_open": 2,
            "activity_count": 3,
            "client_fit_score": 2,
        },
    )
    assert response.status_code == 422
