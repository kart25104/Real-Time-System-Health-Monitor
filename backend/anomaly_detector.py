"""
anomaly_detector.py
--------------------
Wraps scikit-learn's IsolationForest to flag abnormal system readings in real time.

How it works:
1. On startup, we "warm up" the model with a batch of normal-looking readings.
2. Every new reading is scored against the trained model.
3. If the model says a point is an outlier (-1), we flag it as an anomaly.
4. The model is periodically retrained on recent history so it adapts over time
   (this mimics how real production monitoring systems work).
"""

from sklearn.ensemble import IsolationForest
import numpy as np


FEATURES = ["cpu", "memory", "temperature", "latency"]


class AnomalyDetector:
    def __init__(self, contamination: float = 0.06):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
        )
        self.is_trained = False
        self.training_buffer = []

    def _to_vector(self, reading: dict):
        return [reading[f] for f in FEATURES]

    def warm_up(self, readings: list):
        """Train the initial model on a batch of readings collected at startup."""
        if len(readings) < 10:
            return
        X = np.array([self._to_vector(r) for r in readings])
        self.model.fit(X)
        self.is_trained = True

    def retrain(self, readings: list):
        """Retrain periodically on recent history so the model adapts to new baselines."""
        if len(readings) < 20:
            return
        X = np.array([self._to_vector(r) for r in readings])
        self.model.fit(X)
        self.is_trained = True

    def score(self, reading: dict) -> dict:
        """Return the reading enriched with an anomaly flag + confidence score."""
        if not self.is_trained:
            reading["is_anomaly"] = False
            reading["anomaly_score"] = 0.0
            return reading

        X = np.array([self._to_vector(reading)])
        prediction = self.model.predict(X)[0]          # -1 = anomaly, 1 = normal
        raw_score = self.model.decision_function(X)[0]  # lower = more abnormal

        reading["is_anomaly"] = bool(prediction == -1)
        reading["anomaly_score"] = round(float(raw_score), 4)
        return reading