"""
SENTINEL — Standalone training script.

Usage:
    cd backend
    python scripts/train_model.py [--csv PATH] [--model-dir PATH]

Loads configuration from .env, runs the complete training pipeline,
prints final metrics, and saves all artefacts to the models/ directory.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.ml.training import train

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SENTINEL — Train the FraudAutoencoder model"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=str(settings.data_path_resolved),
        help="Path to bank_fraud.csv (default from .env DATA_PATH)",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default=str(settings.model_path_resolved),
        help="Directory to save model artefacts (default from .env MODEL_PATH)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("SENTINEL — FraudAutoencoder Training")
    logger.info(f"  CSV path   : {args.csv}")
    logger.info(f"  Model dir  : {args.model_dir}")
    logger.info("=" * 60)

    result = train(csv_path=args.csv, model_dir=args.model_dir)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Model path       : {result['model_path']}")
    print(f"  Preprocessor     : {result['preprocessor_path']}")
    print(f"  Threshold        : {result['threshold']:.6f}")
    print(f"  Epochs trained   : {result['history_length']}")

    metrics = result.get("metrics", {})
    if metrics:
        print("\n  === Evaluation Metrics ===")
        print(f"  Precision        : {metrics.get('precision', 0):.4f}")
        print(f"  Recall           : {metrics.get('recall', 0):.4f}")
        print(f"  F1 Score         : {metrics.get('f1', 0):.4f}")
        print(f"  ROC-AUC          : {metrics.get('roc_auc', 0):.4f}")
        print(f"  PR-AUC           : {metrics.get('pr_auc', 0):.4f}")
        print(f"  Accuracy         : {metrics.get('accuracy', 0):.4f}")
        cm = metrics.get("confusion_matrix", {})
        print(f"\n  Confusion Matrix:")
        print(f"    TN={cm.get('true_negative', 0):<8} FP={cm.get('false_positive', 0)}")
        print(f"    FN={cm.get('false_negative', 0):<8} TP={cm.get('true_positive', 0)}")
        print(f"\n  Fraud detected   : {metrics.get('fraud_detected', 0):,}")
        print(f"  Fraud missed     : {metrics.get('fraud_missed', 0):,}")

    print("=" * 60)
    logger.info("Training script complete ✓")


if __name__ == "__main__":
    main()
