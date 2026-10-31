import pandas as pd

from bi_agent.analytics import (
    business_metrics,
    flatten_monday_board,
    synthetic_training_data,
)


def test_business_metrics_are_deterministic():
    result = business_metrics(pd.DataFrame({"amount": [10, 20], "status": ["a", None]}))
    assert result["row_count"] == 2
    assert result["numeric_totals"] == {"amount": 30.0}
    assert result["missing_values"] == {"status": 1}


def test_flatten_monday_board():
    result = flatten_monday_board({"data": {"boards": [
        {"name": "Deals", "items_page": {"items": [
            {"name": "Acme", "column_values": [
                {"column": {"title": "Value"}, "text": "100"}
            ]}
        ]}}
    ]}})
    assert result.to_dict("records") == [{"board": "Deals", "item": "Acme", "Value": "100"}]


def test_synthetic_data_reproducible():
    left = synthetic_training_data(seed=7)
    right = synthetic_training_data(seed=7)
    assert left[0].equals(right[0])
    assert left[1].equals(right[1])
