"""
Core AI Predictor — Log anomaly detection and classification.

Pipeline:
  1. Feature extraction from raw log lines
  2. Anomaly detection via IsolationForest (unsupervised)
  3. Error classification via RandomForestClassifier
"""
import json
import logging
import pickle
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# ── Error classification taxonomy ─────────────────────────────────────────────
CLASSIFICATION_PATTERNS: dict[str, list[str]] = {
    "HTTP Error":    [r"\b[45]\d{2}\b", r"http error", r"bad request", r"not found", r"forbidden"],
    "Auth Failure":  [r"auth(entication)? (failed|error|denied)", r"unauthorized", r"access denied", r"invalid (token|credentials|password)", r"login failed"],
    "DB Error":      [r"(sql|mysql|postgres|db|database)\s*(error|exception|fail)", r"connection refused.*\b(3306|5432)\b", r"deadlock", r"query (timeout|fail)"],
    "Timeout":       [r"timeout", r"timed out", r"request took \d+s", r"slow (query|request)"],
    "Memory":        [r"out of memory", r"heap space", r"gc overhead", r"memory (leak|exceeded|limit)", r"oom"],
    "Network":       [r"connection (refused|reset|closed|error)", r"socket (error|timeout|exception)", r"no route to host"],
    "Exception":     [r"exception", r"traceback", r"stack trace", r"unhandled error", r"panic"],
    "Unknown":       [],  # fallback
}

SEVERITY_KEYWORDS = {
    "critical": ["critical", "fatal", "emergency", "panic", "oom", "heap space"],
    "high":     ["error", "exception", "failed", "refused", "denied", "timeout"],
    "medium":   ["warning", "warn", "slow", "retry", "deprecated"],
    "low":      ["info", "debug", "notice"],
}


def _classify_line(line: str) -> str:
    """Rule-based classification (also used to generate training labels)."""
    lower = line.lower()
    for label, patterns in CLASSIFICATION_PATTERNS.items():
        if label == "Unknown":
            continue
        if any(re.search(p, lower) for p in patterns):
            return label
    return "Unknown"


def _severity_from_line(line: str) -> str:
    lower = line.lower()
    for severity, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return severity
    return "low"


class FeatureExtractor:
    """
    Extracts numerical features from a raw log line.
    Designed to be deterministic and fast.
    """

    # Pre-compiled regexes for performance
    _RE_TIMESTAMP  = re.compile(r"\d{2}:\d{2}:\d{2}")
    _RE_IP         = re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b")
    _RE_NUMBER     = re.compile(r"\b\d+\b")
    _RE_HTTP_CODE  = re.compile(r"\b[1-5]\d{2}\b")
    _RE_EXCEPTION  = re.compile(r"(exception|error|traceback|panic)", re.I)
    _RE_HTTP_ERROR = re.compile(r"\b[45]\d{2}\b")
    _RE_LEVEL      = re.compile(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b", re.I)

    LEVEL_SCORES = {"debug": 0, "info": 1, "warn": 2, "warning": 2, "error": 3, "critical": 4, "fatal": 4}

    def extract(self, line: str) -> list[float]:
        lower = line.lower()
        numbers = [int(n) for n in self._RE_NUMBER.findall(line) if len(n) <= 9]

        log_level_match = self._RE_LEVEL.search(line)
        log_level_score = self.LEVEL_SCORES.get(log_level_match.group(1).lower(), 1) if log_level_match else 1

        http_code_match = self._RE_HTTP_CODE.search(line)
        http_code = int(http_code_match.group()) if http_code_match else 0

        return [
            len(line),                                  # f1: line length
            line.count(" "),                            # f2: word count proxy
            log_level_score,                            # f3: log level severity
            1 if self._RE_IP.search(line) else 0,       # f4: has IP
            1 if self._RE_TIMESTAMP.search(line) else 0,# f5: has timestamp
            1 if self._RE_EXCEPTION.search(line) else 0,# f6: has exception keyword
            1 if self._RE_HTTP_ERROR.search(line) else 0,# f7: has HTTP error code
            http_code,                                  # f8: HTTP status code
            max(numbers) if numbers else 0,             # f9: max numeric value
            len(numbers),                               # f10: count of numbers
            lower.count("error"),                       # f11: "error" occurrences
            lower.count("warn"),                        # f12: "warn" occurrences
            len(line.split()),                          # f13: token count
            1 if "]" in line and "[" in line else 0,   # f14: has brackets (structured)
            1 if "stack" in lower or "trace" in lower else 0,  # f15: stack trace indicator
        ]

    @property
    def feature_names(self) -> list[str]:
        return [
            "line_length", "space_count", "log_level_score",
            "has_ip", "has_timestamp", "has_exception", "has_http_error",
            "http_code", "max_number", "number_count",
            "error_count", "warn_count", "token_count",
            "has_brackets", "has_stack_trace",
        ]


class LogPredictor:
    """
    Full ML pipeline:
      - IsolationForest for unsupervised anomaly detection
      - RandomForestClassifier for supervised error classification
      - StandardScaler for feature normalization
    """

    MODEL_VERSION = "2.1.0"

    def __init__(self, model_dir: Path):
        self.model_dir  = model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.extractor   = FeatureExtractor()
        self.scaler      = StandardScaler()
        self.iso_forest  = IsolationForest(contamination=0.05, n_estimators=200, random_state=42, n_jobs=-1)
        self.classifier  = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
        self._trained    = False
        self.version     = self.MODEL_VERSION

    # ── Persistence ────────────────────────────────────────────────────────────
    def _model_paths(self):
        return {
            "scaler":     self.model_dir / "scaler.pkl",
            "iso_forest": self.model_dir / "iso_forest.pkl",
            "classifier": self.model_dir / "classifier.pkl",
        }

    def save(self):
        paths = self._model_paths()
        with open(paths["scaler"],     "wb") as f: pickle.dump(self.scaler,     f)
        with open(paths["iso_forest"], "wb") as f: pickle.dump(self.iso_forest, f)
        with open(paths["classifier"], "wb") as f: pickle.dump(self.classifier, f)
        logger.info("Models saved to %s", self.model_dir)

    def load_or_train(self):
        paths = self._model_paths()
        if all(p.exists() for p in paths.values()):
            try:
                with open(paths["scaler"],     "rb") as f: self.scaler     = pickle.load(f)
                with open(paths["iso_forest"], "rb") as f: self.iso_forest = pickle.load(f)
                with open(paths["classifier"], "rb") as f: self.classifier = pickle.load(f)
                self._trained = True
                logger.info("Loaded pre-trained models from %s", self.model_dir)
                return
            except Exception as exc:
                logger.warning("Model load failed (%s) — retraining", exc)

        logger.info("Training models on synthetic data...")
        self._train_on_synthetic()

    # ── Synthetic training data ────────────────────────────────────────────────
    def _train_on_synthetic(self):
        """
        Generate realistic synthetic log lines and train both models.
        In production, replace with labelled production log data.
        """
        normal_templates = [
            "2024-01-15 {h}:{m}:{s} INFO  RequestHandler - GET /api/v1/users 200 45ms",
            "2024-01-15 {h}:{m}:{s} INFO  Database      - Query executed in 12ms rows=5",
            "2024-01-15 {h}:{m}:{s} DEBUG Scheduler     - Running job cleanup_old_sessions",
            "2024-01-15 {h}:{m}:{s} INFO  Auth          - User admin authenticated successfully",
            "2024-01-15 {h}:{m}:{s} INFO  Cache         - Cache hit for key user:1234",
        ]

        anomaly_templates = [
            "2024-01-15 {h}:{m}:{s} ERROR Database      - Connection refused mysql:3306 after 3 retries",
            "2024-01-15 {h}:{m}:{s} CRITICAL App        - OutOfMemoryError: Java heap space GC overhead exceeded",
            "2024-01-15 {h}:{m}:{s} ERROR Auth          - Authentication failed for user root@10.0.0.5 attempt 5",
            "2024-01-15 {h}:{m}:{s} ERROR HTTP          - 500 Internal Server Error unhandled exception in /api/orders",
            "2024-01-15 {h}:{m}:{s} WARN  DB            - Slow query detected SELECT * FROM logs WHERE ts > ? took 3.2s",
            "2024-01-15 {h}:{m}:{s} ERROR Network       - Socket timeout connecting to cache:6379 after 30000ms",
        ]

        import random
        random.seed(42)
        np.random.seed(42)

        lines, labels = [], []
        for _ in range(4000):
            t = {"h": random.randint(0,23), "m": random.randint(0,59), "s": random.randint(0,59)}
            lines.append(random.choice(normal_templates).format(**t))
            labels.append(0)  # normal
        for _ in range(200):
            t = {"h": random.randint(0,23), "m": random.randint(0,59), "s": random.randint(0,59)}
            lines.append(random.choice(anomaly_templates).format(**t))
            labels.append(1)  # anomaly

        X = np.array([self.extractor.extract(l) for l in lines])
        X_scaled = self.scaler.fit_transform(X)

        # IsolationForest (unsupervised — fit on all)
        self.iso_forest.fit(X_scaled)

        # RandomForest classifier (supervised — fit only on labelled)
        clf_labels = [_classify_line(l) for l in lines]
        self.classifier.fit(X_scaled, clf_labels)

        self._trained = True
        self.save()
        logger.info("✅ Models trained and saved")

    # ── Prediction ─────────────────────────────────────────────────────────────
    def predict(
        self,
        lines: list[str],
        mode: str = "auto",
        sensitivity: int = 7,
    ) -> dict[str, Any]:
        """
        Run anomaly detection + classification on a list of log lines.

        sensitivity (1-10) maps to contamination estimate:
          low sensitivity → fewer anomalies flagged
          high sensitivity → more anomalies flagged
        """
        if not self._trained:
            raise RuntimeError("Models not trained")

        if not lines:
            return {"anomalies": [], "total_lines": 0, "anomaly_rate": 0.0, "model_version": self.version}

        # Feature extraction
        X = np.array([self.extractor.extract(l) for l in lines])
        X_scaled = self.scaler.transform(X)

        # Anomaly scores (lower = more anomalous in IsolationForest)
        scores = self.iso_forest.decision_function(X_scaled)  # shape (n,)
        # Normalize to [0, 1] where 1 = most anomalous
        scores_norm = 1 - (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)

        # Dynamic threshold based on sensitivity (1-10)
        # sensitivity=5 → top ~5%, sensitivity=10 → top ~15%
        threshold_pct = 0.02 + (sensitivity - 1) * 0.015
        threshold = np.percentile(scores_norm, (1 - threshold_pct) * 100)

        # Classifications
        clf_labels = self.classifier.predict(X_scaled)
        clf_probs  = self.classifier.predict_proba(X_scaled).max(axis=1)

        anomalies = []
        for i, (line, score, label, prob) in enumerate(zip(lines, scores_norm, clf_labels, clf_probs)):
            is_anomaly = score >= threshold

            if mode == "anomaly" and not is_anomaly:
                continue
            if mode == "classification" and label == "Unknown":
                continue
            if mode == "auto" and not is_anomaly:
                continue  # only surface anomalies

            severity = _severity_from_line(line)

            anomalies.append({
                "line_number":   i + 1,
                "message":       line[:300],  # truncate long lines
                "severity":      severity,
                "classification": label,
                "confidence":    round(float(prob), 3),
                "anomaly_score": round(float(score), 4),
            })

        # Sort by anomaly score descending
        anomalies.sort(key=lambda a: a["anomaly_score"], reverse=True)

        return {
            "total_lines":   len(lines),
            "anomaly_count": len(anomalies),
            "anomaly_rate":  round(len(anomalies) / max(len(lines), 1), 4),
            "anomalies":     anomalies[:500],  # cap response size
            "model_version": self.version,
        }
