from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def flatten_monday_board(payload: dict[str, Any]) -> pd.DataFrame:
    boards = payload.get("data", {}).get("boards", [])
    rows: list[dict[str, Any]] = []
    for board in boards:
        for item in board.get("items_page", {}).get("items", []):
            row: dict[str, Any] = {"board": board.get("name"), "item": item.get("name")}
            for column in item.get("column_values", []):
                title = column.get("column", {}).get("title")
                if title:
                    row[title] = column.get("text")
            rows.append(row)
    return pd.DataFrame(rows)


def business_metrics(data: dict[str, Any] | pd.DataFrame) -> dict[str, Any]:
    frame = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    if frame.empty:
        return {"row_count": 0, "numeric_totals": {}, "missing_values": {}}
    numeric = frame.select_dtypes(include=[np.number])
    return {
        "row_count": len(frame),
        "numeric_totals": {str(k): float(v) for k, v in numeric.sum().items()},
        "missing_values": {str(k): int(v) for k, v in frame.isna().sum().items() if v},
        "columns": [str(column) for column in frame.columns],
    }


def monday_metrics(data: dict[str, Any]) -> dict[str, Any]:
    frames = [
        flatten_monday_board(payload)
        for payload in data.values()
        if isinstance(payload, dict)
    ]
    frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return business_metrics(frame)


def synthetic_training_data(rows: int = 240, seed: int = 42) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({
        "deal_value": rng.uniform(5_000, 250_000, rows),
        "days_open": rng.integers(1, 180, rows),
        "activity_count": rng.integers(0, 40, rows),
        "client_fit_score": rng.uniform(0, 1, rows),
    })
    logit = (
        0.000012 * frame["deal_value"]
        - 0.012 * frame["days_open"]
        + 0.08 * frame["activity_count"]
        + 2.2 * frame["client_fit_score"]
        - 1.5
    )
    probability = 1 / (1 + np.exp(-logit))
    target = pd.Series((rng.random(rows) < probability).astype(int), name="won")
    return frame, target


def write_synthetic_csv(path: Path, rows: int = 240, seed: int = 42) -> Path:
    features, target = synthetic_training_data(rows, seed)
    result = features.assign(won=target)
    path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(path, index=False)
    return path
