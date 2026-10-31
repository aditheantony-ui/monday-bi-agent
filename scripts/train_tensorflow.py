import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bi_agent.config import get_settings
from bi_agent.ml import train_tensorflow

parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=int, default=5)
args = parser.parse_args()
settings = get_settings()
print(train_tensorflow(settings.model_dir / "tensorflow_deal_outcome.keras", args.epochs))
