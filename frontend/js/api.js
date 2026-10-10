/**
 * CertiFlow API Client
 * Clean abstraction over the REST endpoints with standardized error handling.
 */
const API = {
  BASE_URL: '/api/v1',

  async request(endpoint, options = {}) {
    const config = {
      headers: {
        'Accept': 'application/json',
        ...(options.headers || {})
      },
      ...options
    };

    if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(endpoint, config);
      
      // If response is not JSON (e.g. file or binary)
      const contentType = response.headers.get('content-type') || '';
      if (!response.ok) {
        let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
        if (contentType.includes('application/json')) {
          const errData = await response.json();
          errorDetail = errData.detail || errorDetail;
        } else {
          errorDetail = await response.text();
        }
        throw new Error(errorDetail);
      }

      if (contentType.includes('application/json')) {
        return await response.json();
      }
      return response;
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'} ${endpoint}]:`, err);
      throw err;
    }
  },

  // Health
  async getHealth() {
    return this.request('/health');
  },

  // Jobs
  async createJob(payload) {
    return this.request(`${this.BASE_URL}/jobs`, {
      method: 'POST',
      body: payload
    });
  },

  async getJobs({ status = '', search = '', limit = 50, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    params.append('limit', limit);
    params.append('offset', offset);
    return this.request(`${this.BASE_URL}/jobs?${params.toString()}`);
  },

  async getJobDetail(jobId) {
    return this.request(`${this.BASE_URL}/jobs/${encodeURIComponent(jobId)}`);
  },

  async getJobRecipients(jobId, { status = '', search = '', limit = 100, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    params.append('limit', limit);
    params.append('offset', offset);
    return this.request(`${this.BASE_URL}/jobs/${encodeURIComponent(jobId)}/recipients?${params.toString()}`);
  },

  getJobZipDownloadUrl(jobId) {
    return `${this.BASE_URL}/jobs/${encodeURIComponent(jobId)}/download`;
  },

  getJobCsvExportUrl(jobId) {
    return `${this.BASE_URL}/jobs/${encodeURIComponent(jobId)}/export/csv`;
  },

  getMasterCsvExportUrl() {
    return `${this.BASE_URL}/certificates/export/csv`;
  },

  // Certificates
  async getCertificates({ status = '', search = '', limit = 50, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    params.append('limit', limit);
    params.append('offset', offset);
    return this.request(`${this.BASE_URL}/certificates?${params.toString()}`);
  },

  async getCertificateDetail(certId) {
    return this.request(`${this.BASE_URL}/certificates/${encodeURIComponent(certId)}`);
  },

  getCertificateDownloadUrl(certId) {
    return `${this.BASE_URL}/certificates/${encodeURIComponent(certId)}/download`;
  },

  getSamplePreviewUrl() {
    return `${this.BASE_URL}/certificates/preview/sample`;
  }
};
