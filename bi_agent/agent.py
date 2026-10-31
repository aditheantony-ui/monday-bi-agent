import json
from typing import Any, TypedDict

from .analytics import monday_metrics
from .config import Settings
from .ml import predict_xgboost
from .monday import MondayClient


class AgentState(TypedDict, total=False):
    question: str
    data: dict[str, Any]
    metrics: dict[str, Any]
    answer: str
    provider: str
    prediction: dict[str, float] | None
    prediction_features: dict[str, float] | None


def _answer_with_groq(settings: Settings, context: dict[str, Any], question: str) -> str:
    settings.require_groq()
    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": (
            "You are a careful Monday.com BI assistant. Use only supplied data. "
            "State limitations and do not invent metrics.\nDATA:\n"
            + json.dumps(context, ensure_ascii=False)[:20000]
            + "\nQUESTION:\n" + question
        )}],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def _build_workflow(settings: Settings):
    from langgraph.graph import END, START, StateGraph

    def retrieve(state: AgentState) -> AgentState:
        return {"data": state.get("data") or MondayClient(settings).get_all_data()}

    def analyze(state: AgentState) -> AgentState:
        return {"metrics": monday_metrics(state["data"])}

    def predict(state: AgentState) -> AgentState:
        features = state.get("prediction_features")
        model_path = settings.model_dir / "xgboost_deal_outcome.joblib"
        if not features or not model_path.exists():
            return {"prediction": None}
        return {"prediction": predict_xgboost(model_path, features)}

    def generate(state: AgentState) -> AgentState:
        grounded_context = {
            "data": state["data"],
            "metrics": state["metrics"],
            "prediction": state.get("prediction"),
        }
        return {
            "answer": _answer_with_groq(settings, grounded_context, state["question"]),
            "provider": "groq",
        }

    workflow = StateGraph(AgentState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("analyze", analyze)
    workflow.add_node("predict", predict)
    workflow.add_node("generate", generate)
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "analyze")
    workflow.add_edge("analyze", "predict")
    workflow.add_edge("predict", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


def answer_question(settings: Settings, question: str,
                    data: dict[str, Any] | None = None,
                    prediction_features: dict[str, float] | None = None) -> dict[str, Any]:
    try:
        result = _build_workflow(settings).invoke({
            "question": question,
            "data": data,
            "prediction_features": prediction_features,
        })
        return {
            "answer": result["answer"],
            "provider": result["provider"],
            "data": result["data"],
            "metrics": result["metrics"],
            "prediction": result.get("prediction"),
        }
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("The Groq request failed") from exc


def langgraph_available() -> bool:
    try:
        import langgraph  # noqa: F401
        return True
    except ImportError:
        return False
