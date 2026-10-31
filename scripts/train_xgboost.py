import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bi_agent.config import get_settings
from bi_agent.ml import train_xgboost

parser = argparse.ArgumentParser(description="Train the deal outcome demonstration model.")
parser.add_argument("--data", type=Path, default=None)
parser.add_argument("--output", type=Path, default=None)
args = parser.parse_args()
settings = get_settings()
output = args.output or settings.model_dir / "xgboost_deal_outcome.joblib"
print(train_xgboost(output, args.data))
