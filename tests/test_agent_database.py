from pathlib import Path

from bi_agent.agent import answer_question
from bi_agent.config import Settings
from bi_agent.database import Prediction, create_session_factory, save_prediction


def test_langgraph_workflow_grounds_metrics(monkeypatch):
    data = {
        "deals": {"data": {"boards": [{
            "name": "Deals",
            "items_page": {"items": [{"name": "Acme", "column_values": []}]},
        }]}},
    }
    monkeypatch.setattr(
        "bi_agent.agent._answer_with_groq",
        lambda settings, context, question: str(context["metrics"]["row_count"]),
    )
    result = answer_question(Settings(groq_api_key="test"), "How many deals?", data)
    assert result["answer"] == "1"
    assert result["provider"] == "groq"


def test_langgraph_skips_prediction_without_features(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "bi_agent.agent._answer_with_groq",
        lambda settings, context, question: str(context["prediction"]),
    )
    settings = Settings(groq_api_key="test", model_dir=tmp_path)
    result = answer_question(settings, "Predict?", {"deals": {}}, {"deal_value": 1})
    assert result["prediction"] is None


def test_prediction_repository_persists(tmp_path: Path):
    factory = create_session_factory(f"sqlite:///{tmp_path / 'test.db'}")
    result = {"prediction": 1.0, "probability": 0.75}
    save_prediction(factory, result, {"deal_value": 10.0})
    with factory() as session:
        assert session.query(Prediction).count() == 1
