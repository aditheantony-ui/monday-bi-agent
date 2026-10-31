from pathlib import Path

from bi_agent.ml import predict_xgboost, train_xgboost


def test_xgboost_training_and_inference(tmp_path: Path):
    model_path = tmp_path / "model.joblib"
    result = train_xgboost(model_path)
    assert result["synthetic"] is True
    prediction = predict_xgboost(model_path, {
        "deal_value": 100000, "days_open": 20,
        "activity_count": 10, "client_fit_score": 0.8,
    })
    assert 0 <= prediction["probability"] <= 1
