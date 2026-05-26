/**
 * AI DevOps Log Analyzer — Dashboard Controller
 * Handles all UI logic, page navigation, charts, uploads
 */

/* ============================================================
   UTILITIES
   ============================================================ */

function showToast(message, type = 'info', duration = 4000) {
  const icons = { success: 'fa-check-circle', error: 'fa-times-circle', info: 'fa-info-circle', warning: 'fa-exclamation-triangle' };
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <i class="fas ${icons[type]} toast-icon"></i>
    <span class="toast-message">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function updateClock() {
  const el = document.getElementById('topbar-clock');
  if (el) el.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
}

/* ============================================================
   PAGE NAVIGATION
   ============================================================ */

const pageTitles = {
  dashboard:  'Dashboard',
  upload:     'Upload Logs',
  analyze:    'Analyze',
  results:    'Results',
  history:    'History',
  monitoring: 'Monitoring',
  settings:   'Settings',
};

function navigateTo(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const page = document.getElementById(`page-${pageId}`);
  const navItem = document.querySelector(`.nav-item[data-page="${pageId}"]`);

  if (page) page.classList.add('active');
  if (navItem) navItem.classList.add('active');

  const titleEl = document.getElementById('page-title');
  if (titleEl) titleEl.textContent = pageTitles[pageId] || pageId;

  // Trigger page-specific initializations
  if (pageId === 'dashboard') loadDashboardStats();
  if (pageId === 'analyze')   loadLogSelectorForAnalyze();
  if (pageId === 'history')   loadHistory();
  if (pageId === 'results')   loadLatestResults();
}

/* ============================================================
   CHARTS
   ============================================================ */

let timelineChart = null;
let classChart    = null;

function initCharts() {
  Chart.defaults.color = '#8892a4';
  Chart.defaults.borderColor = '#21293a';
  Chart.defaults.font.family = "'JetBrains Mono', monospace";

  // Timeline chart
  const timelineCtx = document.getElementById('timelineChart')?.getContext('2d');
  if (timelineCtx) {
    const labels = [...Array(7)].map((_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    timelineChart = new Chart(timelineCtx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Anomalies',
            data: [4, 7, 3, 12, 5, 8, 2],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239,68,68,0.08)',
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#ef4444',
            pointRadius: 4,
          },
          {
            label: 'Log Lines',
            data: [1200, 2100, 900, 3400, 1500, 2800, 700],
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59,130,246,0.06)',
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#3b82f6',
            pointRadius: 4,
            yAxisID: 'y2',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2.5,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { padding: 16, usePointStyle: true, pointStyleWidth: 10 } },
          tooltip: {
            backgroundColor: '#161b24',
            borderColor: '#21293a',
            borderWidth: 1,
            titleColor: '#e2e8f0',
            bodyColor: '#8892a4',
          },
        },
        scales: {
          x: { grid: { color: '#21293a' } },
          y: {
            grid: { color: '#21293a' },
            title: { display: true, text: 'Anomalies', color: '#ef4444' },
          },
          y2: {
            position: 'right',
            grid: { drawOnChartArea: false },
            title: { display: true, text: 'Log Lines', color: '#3b82f6' },
          },
        },
      },
    });
  }

  // Classification donut chart
  const classCtx = document.getElementById('classificationChart')?.getContext('2d');
  if (classCtx) {
    classChart = new Chart(classCtx, {
      type: 'doughnut',
      data: {
        labels: ['HTTP Error', 'Auth Failure', 'DB Error', 'Timeout', 'Memory', 'Unknown'],
        datasets: [{
          data: [32, 18, 14, 22, 8, 6],
          backgroundColor: [
            'rgba(239,68,68,0.8)',
            'rgba(245,158,11,0.8)',
            'rgba(139,92,246,0.8)',
            'rgba(59,130,246,0.8)',
            'rgba(6,182,212,0.8)',
            'rgba(74,85,104,0.8)',
          ],
          borderColor: '#161b24',
          borderWidth: 3,
          hoverOffset: 8,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { padding: 12, usePointStyle: true, pointStyleWidth: 10, font: { size: 11 } },
          },
          tooltip: {
            backgroundColor: '#161b24',
            borderColor: '#21293a',
            borderWidth: 1,
          },
        },
        cutout: '62%',
      },
    });
  }
}

/* ============================================================
   DASHBOARD STATS
   ============================================================ */

async function loadDashboardStats() {
  try {
    const data = await StatsAPI.getDashboard();
    animateCounter('stat-total-logs',  data.total_logs      || 0);
    animateCounter('stat-anomalies',   data.total_anomalies || 0);
    animateCounter('stat-analyses',    data.total_analyses  || 0);

    // Show real anomaly rate
    const rateEl = document.getElementById('stat-anomaly-rate');
    if (rateEl) {
      const pct = ((data.avg_anomaly_rate || 0) * 100).toFixed(1);
      rateEl.textContent = `${pct}%`;
    }

    // Update classification chart with real data if available
    if (data.recent_analyses?.length) {
      renderRecentActivity(data.recent_analyses);
      updateClassificationChart(data.recent_analyses);
    }
  } catch {
    // Demo fallback — clearly marked
    animateCounter('stat-total-logs',  0);
    animateCounter('stat-anomalies',   0);
    animateCounter('stat-analyses',    0);
    const rateEl = document.getElementById('stat-anomaly-rate');
    if (rateEl) rateEl.textContent = 'N/A';
  }
}

function updateClassificationChart(analyses) {
  if (!classChart) return;
  // Tally classifications from recent analyses
  const counts = {};
  analyses.forEach(a => {
    if (a.top_classification) {
      counts[a.top_classification] = (counts[a.top_classification] || 0) + 1;
    }
  });
  const labels = Object.keys(counts);
  const values = Object.values(counts);
  if (!labels.length) return;

  classChart.data.labels = labels;
  classChart.data.datasets[0].data = values;
  classChart.update();
}

function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = 0;
  const duration = 1000;
  const startTime = performance.now();
  const isFloat = typeof target === 'string' && target.includes('%');
  const numTarget = isFloat ? parseFloat(target) : parseInt(target);

  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + (numTarget - start) * eased);
    el.textContent = isFloat ? `${(numTarget * eased).toFixed(1)}%` : current.toLocaleString();
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function renderRecentActivity(analyses) {
  const tbody = document.getElementById('recent-activity-body');
  if (!tbody) return;
  tbody.innerHTML = analyses.slice(0, 8).map(a => `
    <tr>
      <td><i class="fas fa-file-alt" style="color:var(--accent-blue); margin-right:6px;"></i>${a.filename}</td>
      <td>${formatDate(a.created_at)}</td>
      <td><span style="font-family:'JetBrains Mono',monospace;">${(a.total_lines || 0).toLocaleString()}</span></td>
      <td><span style="color:var(--accent-red); font-family:'JetBrains Mono',monospace; font-weight:600;">${a.anomaly_count || 0}</span></td>
      <td><span class="badge-status badge-${a.status}">${a.status}</span></td>
      <td>
        <button class="btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="viewResult('${a.id}')">
          <i class="fas fa-eye"></i> View
        </button>
      </td>
    </tr>
  `).join('');

  const badgeEl = document.getElementById('badge-results');
  if (badgeEl) badgeEl.textContent = analyses.length;
}

/* ============================================================
   UPLOAD LOGIC
   ============================================================ */

let uploadQueue = [];

function initUpload() {
  const zone    = document.getElementById('uploadZone');
  const input   = document.getElementById('fileInput');
  const uploadBtn = document.getElementById('uploadBtn');
  const clearBtn  = document.getElementById('clearQueueBtn');

  if (!zone) {
    console.warn('Upload zone element not found');
    return;
  }

  // Validate input element
  if (!input) {
    console.warn('File input element not found');
    return;
  }

  // Drag & drop
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    addFilesToQueue(e.dataTransfer.files);
  });

  zone.addEventListener('click', () => input.click());

  input.addEventListener('change', () => {
    addFilesToQueue(input.files);
    input.value = '';
  });

  // Attach button listeners with validation
  if (uploadBtn) {
    uploadBtn.addEventListener('click', executeUpload);
  } else {
    console.warn('Upload button element not found');
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      uploadQueue = [];
      renderQueue();
    });
  } else {
    console.warn('Clear button element not found');
  }
}

function addFilesToQueue(files) {
  Array.from(files).forEach(f => {
    if (!uploadQueue.find(q => q.name === f.name)) uploadQueue.push(f);
  });
  renderQueue();
}

function renderQueue() {
  const queueEl  = document.getElementById('uploadQueue');
  const listEl   = document.getElementById('queueList');
  if (!queueEl || !listEl) return;

  if (uploadQueue.length === 0) {
    queueEl.style.display = 'none';
    return;
  }

  queueEl.style.display = 'block';
  listEl.innerHTML = uploadQueue.map((f, i) => `
    <div class="queue-item" id="queue-item-${i}">
      <i class="fas fa-file-alt queue-item-icon"></i>
      <span class="queue-item-name">${f.name}</span>
      <span class="queue-item-size">${formatBytes(f.size)}</span>
      <i class="fas fa-times queue-item-remove" onclick="removeFromQueue(${i})"></i>
    </div>
  `).join('');
}

function removeFromQueue(idx) {
  uploadQueue.splice(idx, 1);
  renderQueue();
}

async function executeUpload() {
  if (uploadQueue.length === 0) return showToast('No files in queue', 'warning');

  const uploadBtn  = document.getElementById('uploadBtn');
  const progressEl = document.getElementById('uploadProgress');
  const fillEl     = document.getElementById('progressFill');
  const pctEl      = document.getElementById('progressPct');
  const textEl     = document.getElementById('progressText');

  // Validate required elements exist
  if (!progressEl) {
    showToast('Error: Upload progress element not found', 'error');
    return;
  }

  // Disable button to prevent multiple submissions
  if (uploadBtn) uploadBtn.disabled = true;

  progressEl.style.display = 'block';

  try {
    await LogsAPI.upload(uploadQueue, pct => {
      if (fillEl) fillEl.style.width = `${pct}%`;
      if (pctEl)  pctEl.textContent  = `${pct}%`;
    });

    showToast(`${uploadQueue.length} file(s) uploaded successfully`, 'success');
    uploadQueue = [];
    renderQueue();
    if (textEl) textEl.textContent = 'Upload complete';
    setTimeout(() => { progressEl.style.display = 'none'; }, 2000);
  } catch (err) {
    showToast(`Upload failed: ${err.message}`, 'error');
    progressEl.style.display = 'none';
  } finally {
    // Re-enable button
    if (uploadBtn) uploadBtn.disabled = false;
  }
}

/* ============================================================
   ANALYZE LOGIC
   ============================================================ */

async function loadLogSelectorForAnalyze() {
  const selector = document.getElementById('logSelector');
  if (!selector) return;

  try {
    const logs = await LogsAPI.list();
    if (!logs.length) {
      selector.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i> No logs available. Upload logs first.</div>';
      return;
    }
    selector.innerHTML = logs.map(log => `
      <div class="log-select-item">
        <input type="checkbox" id="log-${log.id}" value="${log.id}" name="log-select"/>
        <label for="log-${log.id}" class="log-name">${log.filename}</label>
        <span class="log-size">${formatBytes(log.file_size)}</span>
        <span class="log-size">${formatDate(log.created_at)}</span>
      </div>
    `).join('');
  } catch {
    selector.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i> Could not load logs</div>';
  }
}

function initAnalyze() {
  const slider  = document.getElementById('sensitivitySlider');
  const valueEl = document.getElementById('sensitivityValue');
  const btn     = document.getElementById('analyzeBtn');

  slider?.addEventListener('input', () => {
    if (valueEl) valueEl.textContent = slider.value;
  });

  btn?.addEventListener('click', async () => {
    const checked = [...document.querySelectorAll('input[name="log-select"]:checked')];
    if (!checked.length) return showToast('Select at least one log file', 'warning');

    const logIds    = checked.map(c => c.value);
    const mode      = document.getElementById('detectionMode')?.value || 'auto';
    const sensitivity = parseInt(document.getElementById('sensitivitySlider')?.value || 7);

    const btnText   = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    btnText.style.display  = 'none';
    btnLoader.style.display = 'flex';
    btn.disabled = true;

    try {
      const result = await AnalysisAPI.analyze({ logIds, mode, sensitivity });
      showToast('Analysis complete!', 'success');
      navigateTo('results');
      loadLatestResults();
    } catch (err) {
      showToast(`Analysis failed: ${err.message}`, 'error');
    } finally {
      btnText.style.display  = 'inline-flex';
      btnLoader.style.display = 'none';
      btn.disabled = false;
    }
  });
}

/* ============================================================
   RESULTS
   ============================================================ */

async function loadLatestResults() {
  const container = document.getElementById('results-content');
  if (!container) return;

  try {
    const results = await AnalysisAPI.listResults();
    if (!results.length) return;
    renderResults(results, container);
  } catch {
    // Show demo result if API unavailable
    renderDemoResult(container);
  }
}

function renderResults(results, container) {
  const latest = results[0];
  container.innerHTML = `
    <div class="result-grid">
      <div class="result-summary-card">
        <div class="stat-label">Total Lines</div>
        <div class="stat-value">${(latest.total_lines || 0).toLocaleString()}</div>
      </div>
      <div class="result-summary-card">
        <div class="stat-label">Anomalies Found</div>
        <div class="stat-value" style="color:var(--accent-red)">${latest.anomaly_count || 0}</div>
      </div>
      <div class="result-summary-card">
        <div class="stat-label">Processing Time</div>
        <div class="stat-value">${latest.processing_time_ms || 0}ms</div>
      </div>
    </div>
    <div class="activity-card">
      <div class="chart-header"><h3>Detected Anomalies — ${latest.filename}</h3></div>
      <div class="anomaly-list">
        ${(latest.anomalies || []).map(a => `
          <div class="anomaly-item">
            <span class="anomaly-severity sev-${a.severity}">${a.severity}</span>
            <span class="anomaly-line">L${a.line_number}</span>
            <span class="anomaly-text">${a.message}</span>
            <span class="anomaly-severity sev-medium">${a.classification}</span>
          </div>
        `).join('') || '<div class="empty-state"><i class="fas fa-shield-alt"></i> No anomalies detected — clean logs!</div>'}
      </div>
    </div>
  `;
}

function renderDemoResult(container) {
  const demoAnomalies = [
    { severity: 'critical', line_number: 142,  message: 'OutOfMemoryError: Java heap space — GC overhead limit exceeded',  classification: 'Memory' },
    { severity: 'high',     line_number: 387,  message: 'Connection refused: Unable to connect to database on port 3306',  classification: 'DB Error' },
    { severity: 'high',     line_number: 521,  message: 'Authentication failed for user admin@192.168.1.55 — 5 attempts',  classification: 'Auth Failure' },
    { severity: 'medium',   line_number: 663,  message: 'Request timeout after 30000ms — /api/v1/analytics endpoint',      classification: 'Timeout' },
    { severity: 'medium',   line_number: 891,  message: 'HTTP 500 Internal Server Error — unhandled exception in handler',  classification: 'HTTP Error' },
    { severity: 'low',      line_number: 1024, message: 'Slow query detected: SELECT * from logs WHERE ... (2.3s)',         classification: 'DB Error' },
  ];

  container.innerHTML = `
    <div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.3); border-radius:8px; padding:12px 16px; margin-bottom:20px; font-size:13px; color:var(--accent-yellow);">
      <i class="fas fa-flask"></i> <strong>Demo Mode</strong> — Connect the backend API to see real results
    </div>
    <div class="result-grid">
      <div class="result-summary-card">
        <div class="stat-label">Total Lines Analyzed</div>
        <div class="stat-value">12,847</div>
      </div>
      <div class="result-summary-card">
        <div class="stat-label">Anomalies Detected</div>
        <div class="stat-value" style="color:var(--accent-red)">6</div>
      </div>
      <div class="result-summary-card">
        <div class="stat-label">Processing Time</div>
        <div class="stat-value">1,240ms</div>
      </div>
    </div>
    <div class="activity-card">
      <div class="chart-header"><h3>Detected Anomalies — app-2024-01-15.log (Demo)</h3></div>
      <div class="anomaly-list">
        ${demoAnomalies.map(a => `
          <div class="anomaly-item">
            <span class="anomaly-severity sev-${a.severity}">${a.severity}</span>
            <span class="anomaly-line">L${a.line_number}</span>
            <span class="anomaly-text">${a.message}</span>
            <span class="anomaly-severity sev-medium">${a.classification}</span>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

/* ============================================================
   HISTORY
   ============================================================ */

async function loadHistory() {
  const tbody = document.getElementById('history-body');
  if (!tbody) return;

  try {
    const results = await AnalysisAPI.listResults();
    if (!results.length) return;
    tbody.innerHTML = results.map((r, i) => `
      <tr>
        <td style="font-family:'JetBrains Mono',monospace; color:var(--text-muted);">#${i + 1}</td>
        <td><i class="fas fa-file-alt" style="color:var(--accent-blue); margin-right:6px;"></i>${r.filename}</td>
        <td>${formatDate(r.created_at)}</td>
        <td style="font-family:'JetBrains Mono',monospace;">${(r.total_lines || 0).toLocaleString()}</td>
        <td style="color:var(--accent-red); font-family:'JetBrains Mono',monospace; font-weight:600;">${r.anomaly_count || 0}</td>
        <td>${r.top_classification || 'N/A'}</td>
        <td style="font-family:'JetBrains Mono',monospace;">${r.processing_time_ms || 0}ms</td>
        <td><span class="badge-status badge-${r.status}">${r.status}</span></td>
        <td>
          <button class="btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="viewResult('${r.id}')">
            <i class="fas fa-eye"></i>
          </button>
          <button class="btn-secondary" style="padding:4px 10px; font-size:11px; margin-left:4px;" onclick="deleteResult('${r.id}')">
            <i class="fas fa-trash"></i>
          </button>
        </td>
      </tr>
    `).join('');

    // Auto-refresh if any analyses are still running
    const hasRunning = results.some(r => r.status === 'pending' || r.status === 'running');
    if (hasRunning) {
      setTimeout(loadHistory, 3000);
    }
  } catch {
    /* empty state stays */
  }
}

function exportHistoryCSV() {
  AnalysisAPI.listResults().then(results => {
    if (!results.length) return showToast('No results to export', 'warning');
    const headers = ['filename','created_at','total_lines','anomaly_count','top_classification','processing_time_ms','status'];
    const rows = results.map(r => headers.map(h => JSON.stringify(r[h] ?? '')).join(','));
    const csv  = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: 'analysis-history.csv' });
    a.click();
    URL.revokeObjectURL(url);
    showToast('CSV exported', 'success');
  }).catch(err => showToast(`Export failed: ${err.message}`, 'error'));
}

async function deleteResult(id) {
  if (!confirm('Delete this analysis result?')) return;
  try {
    await AnalysisAPI.deleteResult(id);
    showToast('Result deleted', 'success');
    loadHistory();
  } catch (err) {
    showToast(`Delete failed: ${err.message}`, 'error');
  }
}

function viewResult(id) {
  const modal   = document.getElementById('resultModal');
  const title   = document.getElementById('modalTitle');
  const body    = document.getElementById('modalBody');
  if (!modal) return;
  title.textContent = `Analysis Result #${id}`;
  body.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:32px;"></i></div>';
  modal.style.display = 'flex';

  AnalysisAPI.getResult(id)
    .then(r => {
      body.innerHTML = `<pre style="font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--text-code); white-space:pre-wrap;">${JSON.stringify(r, null, 2)}</pre>`;
    })
    .catch(err => {
      body.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i> ${err.message}</div>`;
    });
}

/* ============================================================
   HEALTH CHECK
   ============================================================ */

async function checkHealth() {
  const dot  = document.getElementById('api-status-dot');
  const text = document.getElementById('api-status-text');

  const { ok, data } = await HealthAPI.checkBackend();
  if (dot)  dot.className   = `status-dot ${ok ? '' : 'offline'}`;
  if (text) text.textContent = ok ? 'API: Online' : 'API: Offline';

  // Update monitoring page
  const uptimeEl = document.getElementById('mon-api-uptime');
  if (uptimeEl && data?.uptime_seconds != null) {
    const secs = Math.floor(data.uptime_seconds);
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    uptimeEl.textContent = h > 0 ? `${h}h ${m}m` : `${m}m ${s}s`;
  }

  const aiEl = document.getElementById('mon-ai-uptime');
  const { ok: aiOk } = await HealthAPI.checkAI();
  if (aiEl) aiEl.textContent = aiOk ? 'Online' : 'Offline';
}

function saveSettings() {
  const mode = document.getElementById('setting-default-mode')?.value;
  const sens = document.getElementById('setting-sensitivity')?.value;
  if (mode) localStorage.setItem('defaultMode', mode);
  if (sens) localStorage.setItem('defaultSensitivity', sens);
  showToast('Settings saved', 'success');
}

function loadSettings() {
  const mode = localStorage.getItem('defaultMode');
  const sens = localStorage.getItem('defaultSensitivity');
  const modeEl = document.getElementById('setting-default-mode');
  const sensEl = document.getElementById('setting-sensitivity');
  const sensVal = document.getElementById('setting-sensitivity-val');
  if (mode && modeEl) modeEl.value = mode;
  if (sens && sensEl) {
    sensEl.value = sens;
    if (sensVal) sensVal.textContent = sens;
  }
  sensEl?.addEventListener('input', () => {
    if (sensVal) sensVal.textContent = sensEl.value;
  });
}

/* ============================================================
   INIT
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  // Navigation
  document.querySelectorAll('.nav-item[data-page]').forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(item.dataset.page);
    });
  });

  // Navigate from btn links
  document.querySelectorAll('[data-navigate]').forEach(el => {
    el.addEventListener('click', () => navigateTo(el.dataset.navigate));
  });

  // Modal close
  document.getElementById('modalClose')?.addEventListener('click', () => {
    document.getElementById('resultModal').style.display = 'none';
  });
  document.getElementById('resultModal')?.addEventListener('click', e => {
    if (e.target === e.currentTarget) e.currentTarget.style.display = 'none';
  });

  // Sidebar toggle for mobile
  document.getElementById('sidebarToggle')?.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });

  // Chart range buttons
  document.querySelectorAll('.chart-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.chart-controls')?.querySelectorAll('.chart-btn')
        .forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Export CSV
  document.getElementById('exportHistoryBtn')?.addEventListener('click', exportHistoryCSV);

  // Clock
  updateClock();
  setInterval(updateClock, 1000);

  // Health check
  checkHealth();
  setInterval(checkHealth, 30000);

  // Init components
  initCharts();
  initUpload();
  initAnalyze();
  loadSettings();

  // Load initial page
  navigateTo('dashboard');
});
