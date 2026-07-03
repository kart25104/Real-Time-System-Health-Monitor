"""
app.py
------
Flask backend for the Real-Time System Health Monitoring Dashboard.

Endpoints:
    GET /api/servers          -> list of monitored server IDs
    GET /api/metrics/<id>     -> latest reading for one server
    GET /api/history/<id>     -> last N readings for one server (for charts)
    GET /api/alerts           -> recent anomalies across all servers

Runs a background thread that keeps generating + scoring new readings every second,
so the frontend just needs to poll the API to get "real-time" data.
"""

import threading
import time
from collections import deque

from flask import Flask, jsonify
from flask_cors import CORS

from data_simulator import MetricSimulator
from anomaly_detector import AnomalyDetector

app = Flask(__name__)
CORS(app)  # allow the frontend (served separately) to call this API

SERVER_IDS = ["web-server-01", "db-server-01", "api-gateway-01"]
HISTORY_LENGTH = 60  # keep last 60 readings (~1 minute) per server

simulators = {sid: MetricSimulator(sid) for sid in SERVER_IDS}
detectors = {sid: AnomalyDetector() for sid in SERVER_IDS}
history = {sid: deque(maxlen=HISTORY_LENGTH) for sid in SERVER_IDS}
alerts = deque(maxlen=50)

_lock = threading.Lock()


def background_worker():
    """Continuously generates + scores new readings for every simulated server."""
    tick = 0
    while True:
        with _lock:
            for sid in SERVER_IDS:
                reading = simulators[sid].next_reading()
                scored = detectors[sid].score(reading)
                history[sid].append(scored)

                if scored["is_anomaly"]:
                    alerts.appendleft(scored)

            # warm up / retrain each detector once we have enough data
            tick += 1
            if tick == 15:
                for sid in SERVER_IDS:
                    detectors[sid].warm_up(list(history[sid]))
            elif tick > 15 and tick % 30 == 0:
                for sid in SERVER_IDS:
                    detectors[sid].retrain(list(history[sid]))

        time.sleep(1)


@app.route("/api/servers")
def get_servers():
    return jsonify(SERVER_IDS)


@app.route("/api/metrics/<server_id>")
def get_latest_metric(server_id):
    with _lock:
        if server_id not in history or not history[server_id]:
            return jsonify({"error": "no data yet"}), 404
        return jsonify(history[server_id][-1])


@app.route("/api/history/<server_id>")
def get_history(server_id):
    with _lock:
        if server_id not in history:
            return jsonify({"error": "unknown server"}), 404
        return jsonify(list(history[server_id]))


@app.route("/api/alerts")
def get_alerts():
    with _lock:
        return jsonify(list(alerts))


if __name__ == "__main__":
    worker = threading.Thread(target=background_worker, daemon=True)
    worker.start()
    app.run(host="0.0.0.0", port=5000, debug=False)