from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from bi_agent.agent import answer_question, langgraph_available
from bi_agent.analytics import monday_metrics
from bi_agent.config import get_settings
from bi_agent.database import create_session_factory, save_prediction
from bi_agent.ml import FEATURES, predict_xgboost
from bi_agent.monday import MondayClient

app = FastAPI(title="Monday Business Intelligence Agent", version="2.0.0")
settings = get_settings()


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class PredictionRequest(BaseModel):
    deal_value: float = Field(ge=0)
    days_open: float = Field(ge=0)
    activity_count: float = Field(ge=0)
    client_fit_score: float = Field(ge=0, le=1)


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Monday BI Agent Running", "version": app.version}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "langgraph_available": langgraph_available()}


@app.get("/analytics")
def analytics() -> dict[str, Any]:
    try:
        data = MondayClient(settings).get_all_data()
        return {"metrics": monday_metrics(data), "data": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Monday.com analytics unavailable") from exc


@app.get("/test")
def test_monday_connection() -> dict[str, Any]:
    return MondayClient(settings).get_all_data()


@app.post("/agent/query")
@app.post("/ask")
def ask_question(q: Question) -> dict[str, Any]:
    try:
        result = answer_question(settings, q.question)
        return {"answer": result["answer"], "provider": result["provider"]}
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/predictions")
def predict(request: PredictionRequest) -> dict[str, Any]:
    model_path = Path(settings.model_dir) / "xgboost_deal_outcome.joblib"
    if not model_path.exists():
        raise HTTPException(status_code=503, detail="Train the XGBoost model before requesting predictions")
    features = request.model_dump()
    result = predict_xgboost(model_path, features)
    try:
        save_prediction(create_session_factory(settings.database_url), result, features)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Prediction succeeded but persistence failed") from exc
    return {"model": "xgboost-deal-outcome", "features": FEATURES, **result, "synthetic_training": True}
