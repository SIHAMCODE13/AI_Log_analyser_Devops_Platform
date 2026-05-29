/**
 * AI DevOps Log Analyzer â€” API Client
 * Centralized API communication layer
 */

const API_BASE  = window.API_BASE_URL  || '/api/v1';
const AI_BASE   = window.AI_BASE_URL   || 'http://localhost:8001';

class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.defaultHeaders = { 'Content-Type': 'application/json' };
  }

  async request(method, path, { body, headers = {}, isFormData = false } = {}) {
    const url = `${this.baseUrl}${path}`;
    const opts = {
      method,
      headers: isFormData ? headers : { ...this.defaultHeaders, ...headers },
    };
    if (body) opts.body = isFormData ? body : JSON.stringify(body);

    try {
      const res = await fetch(url, opts);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const contentType = res.headers.get('content-type') || '';
      return contentType.includes('application/json') ? res.json() : res.text();
    } catch (err) {
      if (err.name === 'TypeError') throw new Error('Network error â€” is the backend running?');
      throw err;
    }
  }

  get(path, opts)    { return this.request('GET',    path, opts); }
  post(path, opts)   { return this.request('POST',   path, opts); }
  put(path, opts)    { return this.request('PUT',    path, opts); }
  delete(path, opts) { return this.request('DELETE', path, opts); }
}

const backendApi = new ApiClient(API_BASE);
const aiApi      = new ApiClient(AI_BASE);

// ===== LOG API =====
const LogsAPI = {
  /**
   * Upload one or more log files
   * @param {FileList|File[]} files
   * @param {(pct: number) => void} onProgress
   */
  upload(files, onProgress) {
    return new Promise((resolve, reject) => {
      if (!files || files.length === 0) {
        reject(new Error('No files selected'));
        return;
      }

      const formData = new FormData();
      Array.from(files).forEach(f => formData.append('files', f));

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE}/logs/upload`);

      // Track upload progress
      xhr.upload.addEventListener('progress', e => {
        if (e.lengthComputable && onProgress) {
          const percentage = Math.round((e.loaded / e.total) * 100);
          onProgress(percentage);
        }
      });

      // Handle successful response
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            reject(new Error('Invalid response from server'));
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
        }
      });

      // Handle network errors
      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload â€” is the backend running?'));
      });

      // Handle abort
      xhr.addEventListener('abort', () => {
        reject(new Error('Upload cancelled'));
      });

      // Send the request
      xhr.send(formData);
    });
  },

  list()           { return backendApi.get('/logs'); },
  get(id)          { return backendApi.get(`/logs/${id}`); },
  delete(id)       { return backendApi.delete(`/logs/${id}`); },
};

// ===== ANALYSIS API =====
const AnalysisAPI = {
  /**
   * Trigger analysis for given log IDs
   */
  analyze({ logIds, mode = 'auto', sensitivity = 7 }) {
    return backendApi.post('/analyze', {
      body: { log_ids: logIds, mode, sensitivity },
    });
  },

  listResults()    { return backendApi.get('/results'); },
  getResult(id)    { return backendApi.get(`/results/${id}`); },
  deleteResult(id) { return backendApi.delete(`/results/${id}`); },
};

// ===== HEALTH API =====
const HealthAPI = {
  async checkBackend() {
    try {
      const data = await backendApi.get('/health');
      return { ok: true, data };
    } catch {
      return { ok: false };
    }
  },

  async checkAI() {
    try {
      const data = await aiApi.get('/health');
      return { ok: true, data };
    } catch {
      return { ok: false };
    }
  },
};

// ===== STATS API =====
const StatsAPI = {
  getDashboard() { return backendApi.get('/stats/dashboard'); },
};
