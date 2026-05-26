"""
AI Service Tests — predictor unit tests
"""
import pytest
from pathlib import Path
import tempfile

from app.services.predictor import LogPredictor, FeatureExtractor, _classify_line


def test_feature_extractor():
    ext = FeatureExtractor()
    features = ext.extract("2024-01-15 10:30:00 ERROR Auth - Login failed for user admin")
    assert len(features) == 15
    assert all(isinstance(f, (int, float)) for f in features)


def test_classify_line_http_error():
    assert _classify_line("GET /api/users 404 Not Found") == "HTTP Error"


def test_classify_line_auth_failure():
    assert _classify_line("Authentication failed for user root") == "Auth Failure"


def test_classify_line_db_error():
    assert _classify_line("MySQL connection refused on port 3306") == "DB Error"


def test_classify_line_timeout():
    assert _classify_line("Request timeout after 30000ms") == "Timeout"


def test_classify_line_memory():
    assert _classify_line("OutOfMemoryError: Java heap space") == "Memory"


def test_predictor_train_and_predict():
    with tempfile.TemporaryDirectory() as tmpdir:
        predictor = LogPredictor(model_dir=Path(tmpdir))
        predictor.load_or_train()
        assert predictor._trained

        # Test with normal and anomalous lines
        lines = [
            "2024-01-15 10:00:00 INFO App - User logged in successfully",
            "2024-01-15 10:00:01 INFO App - Processed 100 records in 12ms",
            "2024-01-15 10:00:02 ERROR App - OutOfMemoryError: Java heap space exceeded",
            "2024-01-15 10:00:03 CRITICAL DB - Connection refused mysql:3306 after 5 retries",
        ]

        result = predictor.predict(lines, mode="auto", sensitivity=7)

        assert "anomalies" in result
        assert "total_lines" in result
        assert result["total_lines"] == 4
        assert isinstance(result["anomaly_rate"], float)


def test_predictor_empty_input():
    with tempfile.TemporaryDirectory() as tmpdir:
        predictor = LogPredictor(model_dir=Path(tmpdir))
        predictor.load_or_train()
        result = predictor.predict([], mode="auto")
        assert result["total_lines"] == 0
        assert result["anomalies"] == []
