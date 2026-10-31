# Monday Business Intelligence AI Agent

This project combines the existing Monday.com GraphQL integration, Groq-powered
question answering, FastAPI backend, and Streamlit frontend with deterministic
analytics, an XGBoost demonstration model, optional TensorFlow and PySpark
pipelines, and SQLAlchemy persistence.

## Architecture

- `main.py`: validated FastAPI application and compatibility routes (`/ask`, `/test`).
- `bi_agent/monday.py`: Monday.com GraphQL client.
- `bi_agent/agent.py`: LangGraph `retrieve -> analyze -> predict -> generate`
  workflow and Groq response generation. The prediction node runs only when
  feature values and a trained XGBoost artifact are available; otherwise it
  records no prediction rather than inventing one.
- `bi_agent/analytics.py`: Pandas/NumPy metrics and reproducible synthetic data.
- `bi_agent/ml.py`: XGBoost training/inference, optional TensorFlow training
  with held-out evaluation, and PySpark cleaning/numeric aggregation.
- `bi_agent/database.py`: SQLAlchemy schema for board snapshots and prediction history.
- `streamlit_app.py`: existing Streamlit UI, optionally connected to the backend.

The XGBoost and TensorFlow examples use synthetic data when no historical
labelled dataset is supplied. Their metrics and predictions are demonstrations,
not evidence of real business performance.

## Requirements and setup

Python 3.12 is recommended for the broadest optional dependency support.
Python 3.14 works for the core application and XGBoost path in the provided
environment. TensorFlow and PySpark are optional and may require a compatible
Python release plus Java for Spark.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Fill `.env` with newly rotated credentials. Never commit `.env`. The
`DATABASE_URL` default uses local SQLite so tests and development do not need
MySQL. For MySQL, use a URL such as
`mysql+pymysql://user:password@localhost:3306/monday_bi`. The compatible
PyMySQL driver is included in the core requirements.

## Commands

Initialize the configured database (table creation occurs on first prediction):

```powershell
python -c "from bi_agent.config import get_settings; from bi_agent.database import create_session_factory; create_session_factory(get_settings().database_url)"
```

Train and evaluate the XGBoost demonstration model:

```powershell
python scripts\train_xgboost.py
```

Use a real labelled CSV with columns `deal_value,days_open,activity_count,client_fit_score,won`:

```powershell
python scripts\train_xgboost.py --data data\deals.csv
```

Optional TensorFlow experiment:

```powershell
python -m pip install -r requirements-tensorflow.txt
python scripts\train_tensorflow.py --epochs 5
```

The TensorFlow script saves both a `.keras` model and an
`.evaluation.json` report. Its default dataset is synthetic.

Optional PySpark processing:

```powershell
python -m pip install -r requirements-pyspark.txt
python scripts\process_spark.py data\deals.csv data\deals-processed.csv
```

The Spark script removes fully empty rows and aggregates numeric columns. A
compatible Java runtime is required for local Spark execution.

Start the backend and frontend:

```powershell
python -m uvicorn main:app --reload
streamlit run streamlit_app.py
```

Set `BACKEND_URL=http://localhost:8000` in `.env` to make Streamlit use the
FastAPI agent endpoint. Without it, the existing direct Streamlit/Monday/Groq
path remains available.

## API

- `GET /health`: import-safe health check.
- `GET /analytics`: fetch Monday boards and return deterministic metrics.
- `POST /agent/query` or `POST /ask`: body `{"question":"..."}`.
- `POST /predictions`: body with `deal_value`, `days_open`, `activity_count`,
  and `client_fit_score` between 0 and 1. Train the model first.
- `GET /test`: compatibility Monday.com connection check.

## Testing and CI

```powershell
python -m pytest -q
ruff check .
```

GitHub Actions runs dependency installation, Ruff, and pytest on every push and
pull request. Tests mock or avoid external services and do not require real
API keys, MySQL, TensorFlow, or Spark.

## Troubleshooting

- A missing Monday or Groq key is reported only when that integration is used.
- A prediction request returns `503` until the XGBoost model is trained.
- TensorFlow and PySpark are intentionally lazy imports; install their optional
  requirement files only when those experiments are needed.
- For MySQL connection problems, verify the server, database, URL encoding,
  and `DATABASE_URL`; local SQLite is the default fallback for development.
