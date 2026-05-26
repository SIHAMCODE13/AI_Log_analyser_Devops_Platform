"""
AI Log Analyzer — Standalone Training Script
Use this to train models on your real log data before deployment.

Usage:
    python training/train.py --data-dir /path/to/logs --output-dir /app/models

The script expects CSV files with columns:
  - log_line (str): raw log line
  - label    (str): classification label (optional; auto-detected if absent)
  - is_anomaly (int): 0 or 1 (optional)
"""
import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.predictor import FeatureExtractor, _classify_line, LogPredictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_data(data_dir: Path) -> pd.DataFrame:
    """Load all CSV log data files from a directory."""
    dfs = []
    for csv_file in data_dir.glob("*.csv"):
        logger.info("Loading %s", csv_file)
        df = pd.read_csv(csv_file)
        dfs.append(df)
    if not dfs:
        raise ValueError(f"No CSV files found in {data_dir}")
    df = pd.concat(dfs, ignore_index=True)
    logger.info("Loaded %d total log lines", len(df))
    return df


def generate_synthetic_dataset(n_normal: int = 10000, n_anomaly: int = 500) -> pd.DataFrame:
    """Generate a synthetic training dataset for demonstration."""
    import random
    random.seed(42)

    normal_templates = [
        "2024-01-15 {H}:{M}:{S} INFO  RequestHandler - GET /api/v1/users 200 {ms}ms user_id={uid}",
        "2024-01-15 {H}:{M}:{S} INFO  Database      - Query executed in {ms}ms rows={n}",
        "2024-01-15 {H}:{M}:{S} DEBUG Cache         - Cache HIT key=session:{uid} ttl={n}s",
        "2024-01-15 {H}:{M}:{S} INFO  Auth          - Token validated for user {uid}",
        "2024-01-15 {H}:{M}:{S} INFO  Worker        - Batch job completed: processed {n} records",
    ]
    anomaly_templates = [
        "2024-01-15 {H}:{M}:{S} ERROR Database   - Connection refused mysql:3306 attempt {n}",
        "2024-01-15 {H}:{M}:{S} CRITICAL App    - OutOfMemoryError heap space GC overhead",
        "2024-01-15 {H}:{M}:{S} ERROR Auth      - Authentication FAILED user=root@{ip} attempt {n}",
        "2024-01-15 {H}:{M}:{S} ERROR HTTP      - 500 Internal Server Error /api/orders unhandled exception",
        "2024-01-15 {H}:{M}:{S} WARN  DB        - Slow query {ms}ms SELECT * FROM logs WHERE ts > ?",
        "2024-01-15 {H}:{M}:{S} ERROR Network   - Socket timeout redis:{port} after 30000ms",
    ]

    def rnd():
        return {
            "H": random.randint(0, 23), "M": random.randint(0, 59), "S": random.randint(0, 59),
            "ms": random.randint(100, 5000), "n": random.randint(1, 1000),
            "uid": random.randint(1000, 9999), "ip": f"10.0.{random.randint(0,255)}.{random.randint(1,254)}",
            "port": random.choice([6379, 5432, 3306]),
        }

    rows = []
    for _ in range(n_normal):
        line = random.choice(normal_templates).format(**rnd())
        rows.append({"log_line": line, "label": _classify_line(line), "is_anomaly": 0})
    for _ in range(n_anomaly):
        line = random.choice(anomaly_templates).format(**rnd())
        rows.append({"log_line": line, "label": _classify_line(line), "is_anomaly": 1})

    return pd.DataFrame(rows)


def train(data: pd.DataFrame, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    extractor = FeatureExtractor()

    logger.info("Extracting features from %d lines...", len(data))
    X = np.array([extractor.extract(line) for line in data["log_line"]])
    y_class = data["label"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ── IsolationForest ───────────────────────────────────────────────────────
    logger.info("Training IsolationForest...")
    iso = IsolationForest(contamination=0.05, n_estimators=300, random_state=42, n_jobs=-1)
    iso.fit(X_scaled)
    logger.info("IsolationForest training complete")

    # ── RandomForest Classifier ───────────────────────────────────────────────
    logger.info("Training RandomForestClassifier...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_class, test_size=0.2, random_state=42, stratify=y_class
    )
    clf = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1, class_weight="balanced")
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    logger.info("Classification Report:\n%s", classification_report(y_test, y_pred))

    # ── Save models ───────────────────────────────────────────────────────────
    predictor = LogPredictor(model_dir=output_dir)
    predictor.scaler     = scaler
    predictor.iso_forest = iso
    predictor.classifier = clf
    predictor._trained   = True
    predictor.save()

    logger.info("✅ Models saved to %s", output_dir)
    return clf.classes_


def main():
    parser = argparse.ArgumentParser(description="Train AI log analyzer models")
    parser.add_argument("--data-dir",   type=Path, help="Directory with CSV training data")
    parser.add_argument("--output-dir", type=Path, default=Path("../models"), help="Model output directory")
    parser.add_argument("--synthetic",  action="store_true", help="Use synthetic training data")
    parser.add_argument("--n-normal",   type=int, default=10000)
    parser.add_argument("--n-anomaly",  type=int, default=500)
    args = parser.parse_args()

    if args.synthetic or not args.data_dir:
        logger.info("Generating synthetic dataset (n_normal=%d, n_anomaly=%d)", args.n_normal, args.n_anomaly)
        data = generate_synthetic_dataset(args.n_normal, args.n_anomaly)
    else:
        data = load_data(args.data_dir)

    classes = train(data, args.output_dir)
    logger.info("Training complete. Classes: %s", list(classes))


if __name__ == "__main__":
    main()
