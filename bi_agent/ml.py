import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from .analytics import synthetic_training_data

FEATURES = ["deal_value", "days_open", "activity_count", "client_fit_score"]


def train_xgboost(model_path: Path, data_path: Path | None = None, seed: int = 42) -> dict[str, Any]:
    if data_path:
        dataset = pd.read_csv(data_path)
        features = dataset[FEATURES]
        target = dataset["won"]
        source = str(data_path)
    else:
        features, target = synthetic_training_data(seed=seed)
        source = "synthetic demonstration data"
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=seed, stratify=target
    )
    model = XGBClassifier(
        n_estimators=120, max_depth=3, learning_rate=0.06,
        subsample=0.85, colsample_bytree=0.85, eval_metric="logloss",
        random_state=seed, n_jobs=1,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    report = {
        "model_path": str(model_path),
        "data_source": source,
        "synthetic": data_path is None,
        "accuracy": float(accuracy_score(y_test, predictions)),
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "test_rows": len(y_test),
    }
    report_path = model_path.with_suffix(".evaluation.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {**report, "evaluation_report": str(report_path)}


def predict_xgboost(model_path: Path, features: dict[str, float]) -> dict[str, float]:
    model = joblib.load(model_path)
    frame = pd.DataFrame([{name: float(features[name]) for name in FEATURES}])
    probability = float(model.predict_proba(frame)[0, 1])
    return {"probability": probability, "prediction": float(probability >= 0.5)}


def train_tensorflow(model_path: Path, epochs: int = 5, seed: int = 42) -> dict[str, Any]:
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError("TensorFlow is optional; install requirements-tensorflow.txt") from exc
    tf.random.set_seed(seed)
    features, target = synthetic_training_data(seed=seed)
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=seed, stratify=target
    )
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(len(FEATURES),)),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    history = model.fit(x_train, y_train, epochs=epochs, batch_size=32, verbose=0)
    loss, accuracy = model.evaluate(x_test, y_test, verbose=0)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)
    report = {
        "model_path": str(model_path),
        "synthetic": True,
        "epochs": epochs,
        "test_rows": len(y_test),
        "final_train_accuracy": float(history.history["accuracy"][-1]),
        "test_loss": float(loss),
        "test_accuracy": float(accuracy),
    }
    report_path = model_path.with_suffix(".evaluation.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {**report, "evaluation_report": str(report_path)}


def process_with_spark(frame: pd.DataFrame) -> pd.DataFrame:
    try:
        from pyspark.sql import SparkSession
    except ImportError as exc:
        raise RuntimeError("PySpark is optional; install requirements-pyspark.txt") from exc
    spark = SparkSession.builder.master("local[2]").appName("monday-bi-agent").getOrCreate()
    try:
        cleaned = frame.dropna(how="all")
        from pyspark.sql.types import DoubleType, StringType, StructField, StructType

        numeric_columns = [
            column for column, dtype in cleaned.dtypes.items()
            if pd.api.types.is_numeric_dtype(dtype)
        ]
        schema = StructType([
            StructField(
                str(column),
                DoubleType() if column in numeric_columns else StringType(),
                True,
            )
            for column in cleaned.columns
        ])
        records = []
        for values in cleaned.itertuples(index=False, name=None):
            normalized = []
            for value, column in zip(values, cleaned.columns):
                if pd.isna(value):
                    normalized.append(None)
                elif column in numeric_columns:
                    normalized.append(float(value))
                else:
                    normalized.append(str(value))
            records.append(tuple(normalized))
        spark_frame = spark.createDataFrame(records, schema=schema)
        if not numeric_columns:
            return pd.DataFrame([row.asDict() for row in spark_frame.collect()])
        aggregated = spark_frame.groupBy().sum(*numeric_columns).collect()[0].asDict()
        return pd.DataFrame([{
            column: aggregated.get(f"sum({column})")
            for column in numeric_columns
        }])
    finally:
        spark.stop()
