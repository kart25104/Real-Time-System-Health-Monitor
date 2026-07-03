"""
data_simulator.py
------------------
Simulates real-time system health metrics (CPU %, Memory %, Temperature, Network Latency)
for multiple virtual "servers" — no real hardware required.

Occasionally injects anomaly spikes so the ML model has something real to detect.
"""

import random
import time


class MetricSimulator:
    def __init__(self, server_id: str):
        self.server_id = server_id
        # baseline "normal" values for this server
        self.cpu = random.uniform(20, 40)
        self.memory = random.uniform(30, 50)
        self.temperature = random.uniform(40, 55)
        self.latency = random.uniform(10, 30)

    def _drift(self, value, min_v, max_v, step=3):
        """Random walk to make metrics look organic instead of pure random noise."""
        value += random.uniform(-step, step)
        return max(min_v, min(max_v, value))

    def next_reading(self, anomaly_chance: float = 0.05) -> dict:
        """Generate the next reading. Occasionally spikes to simulate a real anomaly."""
        self.cpu = self._drift(self.cpu, 10, 95)
        self.memory = self._drift(self.memory, 15, 95)
        self.temperature = self._drift(self.temperature, 30, 90)
        self.latency = self._drift(self.latency, 5, 200, step=5)

        is_injected_anomaly = random.random() < anomaly_chance
        if is_injected_anomaly:
            # simulate a real failure scenario: CPU/temp spike or latency spike
            spike_type = random.choice(["cpu_spike", "temp_spike", "latency_spike"])
            if spike_type == "cpu_spike":
                self.cpu = random.uniform(90, 100)
            elif spike_type == "temp_spike":
                self.temperature = random.uniform(85, 100)
            else:
                self.latency = random.uniform(250, 400)

        return {
            "server_id": self.server_id,
            "timestamp": time.time(),
            "cpu": round(self.cpu, 2),
            "memory": round(self.memory, 2),
            "temperature": round(self.temperature, 2),
            "latency": round(self.latency, 2),
        }