// script.js
// Polls the Flask backend every 2 seconds and updates the dashboard live.

const API_BASE = "http://localhost:5000";
const POLL_INTERVAL_MS = 2000;

let currentServer = null;
let chart = null;

async function fetchServers() {
  const res = await fetch(`${API_BASE}/api/servers`);
  const servers = await res.json();
  renderServerTabs(servers);
  currentServer = servers[0];
  initChart();
  startPolling();
}

function renderServerTabs(servers) {
  const container = document.getElementById("server-tabs");
  container.innerHTML = "";
  servers.forEach((sid, idx) => {
    const tab = document.createElement("div");
    tab.className = "server-tab" + (idx === 0 ? " active" : "");
    tab.textContent = sid;
    tab.onclick = () => {
      document.querySelectorAll(".server-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentServer = sid;
      chart.data.labels = [];
      chart.data.datasets.forEach(ds => ds.data = []);
    };
    container.appendChild(tab);
  });
}

function initChart() {
  const ctx = document.getElementById("metricsChart").getContext("2d");
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "CPU %", data: [], borderColor: "#4fd1c5", tension: 0.3, pointRadius: 0 },
        { label: "Memory %", data: [], borderColor: "#63b3ed", tension: 0.3, pointRadius: 0 },
        { label: "Temperature °C", data: [], borderColor: "#f6ad55", tension: 0.3, pointRadius: 0 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { ticks: { color: "#8891a7" }, grid: { color: "#262f45" } },
        y: { ticks: { color: "#8891a7" }, grid: { color: "#262f45" }, min: 0, max: 100 },
      },
      plugins: {
        legend: { labels: { color: "#e6e9f0" } },
      },
    },
  });
}

async function pollMetrics() {
  if (!currentServer) return;
  try {
    const res = await fetch(`${API_BASE}/api/metrics/${currentServer}`);
    const data = await res.json();
    updateCards(data);
    updateChart(data);
  } catch (err) {
    console.error("Failed to fetch metrics:", err);
  }

  try {
    const alertsRes = await fetch(`${API_BASE}/api/alerts`);
    const alerts = await alertsRes.json();
    updateAlertsTable(alerts);
  } catch (err) {
    console.error("Failed to fetch alerts:", err);
  }
}

function updateCards(data) {
  document.getElementById("cpu-value").textContent = `${data.cpu}%`;
  document.getElementById("memory-value").textContent = `${data.memory}%`;
  document.getElementById("temperature-value").textContent = `${data.temperature}°C`;
  document.getElementById("latency-value").textContent = `${data.latency} ms`;

  const cpuCard = document.getElementById("cpu-value").parentElement;
  cpuCard.classList.toggle("pulse", data.is_anomaly);
}

function updateChart(data) {
  const label = new Date(data.timestamp * 1000).toLocaleTimeString();
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(data.cpu);
  chart.data.datasets[1].data.push(data.memory);
  chart.data.datasets[2].data.push(data.temperature);

  // keep last 30 points visible
  if (chart.data.labels.length > 30) {
    chart.data.labels.shift();
    chart.data.datasets.forEach(ds => ds.data.shift());
  }
  chart.update();
}

function updateAlertsTable(alerts) {
  const tbody = document.getElementById("alerts-body");
  tbody.innerHTML = "";
  alerts.slice(0, 15).forEach(a => {
    const row = document.createElement("tr");
    row.className = "anomaly-row";
    row.innerHTML = `
      <td>${new Date(a.timestamp * 1000).toLocaleTimeString()}</td>
      <td>${a.server_id}</td>
      <td>${a.cpu}%</td>
      <td>${a.memory}%</td>
      <td>${a.temperature}°C</td>
      <td>${a.latency} ms</td>
      <td>${a.anomaly_score}</td>
    `;
    tbody.appendChild(row);
  });
}

function startPolling() {
  pollMetrics();
  setInterval(pollMetrics, POLL_INTERVAL_MS);
}

fetchServers();