/**
 * CertiFlow Application Controller
 * Handles view routing, dynamic UI tables, CSV parsing, live polling, and API interactions.
 */

class CertiFlowApp {
  constructor() {
    this.currentView = 'dashboard';
    this.activeJobId = null;
    this.pollIntervalId = null;
    this.pollFailCount = 0;
    this.recipientsData = [];

    this.initElements();
    this.bindEvents();
    this.checkHealth();
    this.setupInitialRecipients();
    this.navigateTo('dashboard');
  }

  initElements() {
    // Navigation
    this.navItems = document.querySelectorAll('.nav-item');
    this.viewSections = document.querySelectorAll('.view-section');
    this.pageTitle = document.getElementById('pageTitle');
    this.pageSubtitle = document.getElementById('pageSubtitle');
    this.btnRefreshCurrent = document.getElementById('btnRefreshCurrent');
    this.btnTopCreateJob = document.getElementById('btnTopCreateJob');
    this.systemStatusDot = document.getElementById('systemStatusDot');
    this.systemStatusText = document.getElementById('systemStatusText');

    // Dashboard
    this.kpiTotalJobs = document.getElementById('kpiTotalJobs');
    this.kpiTotalGenerated = document.getElementById('kpiTotalGenerated');
    this.kpiInProgress = document.getElementById('kpiInProgress');
    this.kpiTotalFailed = document.getElementById('kpiTotalFailed');
    this.dashboardJobsTbody = document.getElementById('dashboardJobsTbody');
    this.btnViewAllJobs = document.getElementById('btnViewAllJobs');

    // Create Job
    this.createJobForm = document.getElementById('createJobForm');
    this.recipientsInputTbody = document.getElementById('recipientsInputTbody');
    this.btnAddRecipientRow = document.getElementById('btnAddRecipientRow');
    this.btnDownloadSampleCsv = document.getElementById('btnDownloadSampleCsv');
    this.csvFileInput = document.getElementById('csvFileInput');
    this.btnResetJobForm = document.getElementById('btnResetJobForm');
    this.recipientCountDisplay = document.getElementById('recipientCountDisplay');
    this.clientValidationStatus = document.getElementById('clientValidationStatus');

    // Jobs List
    this.jobsSearchInput = document.getElementById('jobsSearchInput');
    this.jobsStatusFilter = document.getElementById('jobsStatusFilter');
    this.jobsListTbody = document.getElementById('jobsListTbody');

    // Job Details
    this.btnBackToJobs = document.getElementById('btnBackToJobs');
    this.jobDetailId = document.getElementById('jobDetailId');
    this.jobDetailMetaChips = document.getElementById('jobDetailMetaChips');
    this.jobDetailProgressPct = document.getElementById('jobDetailProgressPct');
    this.jobDetailProgressBar = document.getElementById('jobDetailProgressBar');
    this.chipCompletedCount = document.getElementById('chipCompletedCount');
    this.chipFailedCount = document.getElementById('chipFailedCount');
    this.chipProcessingCount = document.getElementById('chipProcessingCount');
    this.chipPendingCount = document.getElementById('chipPendingCount');
    this.jobPollingIndicator = document.getElementById('jobPollingIndicator');
    this.btnDownloadJobZip = document.getElementById('btnDownloadJobZip');
    this.btnExportJobCsv = document.getElementById('btnExportJobCsv');
    this.jobRecipientsSearch = document.getElementById('jobRecipientsSearch');
    this.jobRecipientsFilter = document.getElementById('jobRecipientsFilter');
    this.jobRecipientsTbody = document.getElementById('jobRecipientsTbody');

    // Certificates Vault
    this.certSearchInput = document.getElementById('certSearchInput');
    this.certStatusFilter = document.getElementById('certStatusFilter');
    this.btnExportMasterCsv = document.getElementById('btnExportMasterCsv');
    this.certificatesListTbody = document.getElementById('certificatesListTbody');

    // Modal
    this.confirmModal = document.getElementById('confirmModal');
    this.modalContent = document.getElementById('modalContent');
    this.btnModalClose = document.getElementById('btnModalClose');
    this.btnModalCancel = document.getElementById('btnModalCancel');
    this.btnModalConfirm = document.getElementById('btnModalConfirm');
    this.pendingSubmissionData = null;

    // Toast
    this.toastContainer = document.getElementById('toastContainer');
  }

  bindEvents() {
    // Navigation
    this.navItems.forEach(item => {
      item.addEventListener('click', () => {
        const targetView = item.getAttribute('data-view');
        this.navigateTo(targetView);
      });
    });

    this.btnRefreshCurrent.addEventListener('click', () => this.refreshCurrentView());
    this.btnTopCreateJob.addEventListener('click', () => this.navigateTo('create-job'));
    this.btnViewAllJobs.addEventListener('click', () => this.navigateTo('jobs'));
    this.btnBackToJobs.addEventListener('click', () => this.navigateTo('jobs'));

    // Create Job Table
    this.btnAddRecipientRow.addEventListener('click', () => this.addRecipientRow());
    this.btnDownloadSampleCsv.addEventListener('click', () => this.downloadSampleCsv());
    this.csvFileInput.addEventListener('change', (e) => this.handleCsvUpload(e));
    this.btnResetJobForm.addEventListener('click', () => this.resetCreateJobForm());
    this.createJobForm.addEventListener('submit', (e) => this.handleJobFormSubmit(e));

    // Modal Actions
    this.btnModalClose.addEventListener('click', () => this.hideModal());
    this.btnModalCancel.addEventListener('click', () => this.hideModal());
    this.btnModalConfirm.addEventListener('click', () => this.confirmAndSubmitJob());

    // Filters & Searches
    this.jobsSearchInput.addEventListener('input', () => this.loadJobs());
    this.jobsStatusFilter.addEventListener('change', () => this.loadJobs());

    this.jobRecipientsSearch.addEventListener('input', () => this.loadJobRecipients());
    this.jobRecipientsFilter.addEventListener('change', () => this.loadJobRecipients());

    this.certSearchInput.addEventListener('input', () => this.loadCertificates());
    this.certStatusFilter.addEventListener('change', () => this.loadCertificates());

    // Bulk Zip & CSV Export
    this.btnDownloadJobZip.addEventListener('click', () => {
      if (this.activeJobId) {
        window.location.href = API.getJobZipDownloadUrl(this.activeJobId);
      }
    });

    this.btnExportJobCsv.addEventListener('click', () => {
      if (this.activeJobId) {
        window.location.href = API.getJobCsvExportUrl(this.activeJobId);
      }
    });

    this.btnExportMasterCsv.addEventListener('click', () => {
      window.location.href = API.getMasterCsvExportUrl();
    });
  }

  async checkHealth() {
    try {
      const data = await API.getHealth();
      if (data.status === 'healthy') {
        this.systemStatusDot.className = 'status-indicator online';
        this.systemStatusText.textContent = `Online (${data.database})`;
      } else {
        this.systemStatusDot.className = 'status-indicator';
        this.systemStatusDot.style.backgroundColor = '#EAB308';
        this.systemStatusText.textContent = 'Degraded';
      }
    } catch (e) {
      this.systemStatusDot.className = 'status-indicator';
      this.systemStatusDot.style.backgroundColor = '#EF4444';
      this.systemStatusText.textContent = 'Offline';
    }
  }

  // Navigation Controller
  navigateTo(viewName, params = {}) {
    this.stopPolling();
    this.currentView = viewName;

    this.navItems.forEach(item => {
      if (item.getAttribute('data-view') === viewName) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    this.viewSections.forEach(section => {
      section.classList.remove('active');
    });

    const targetSection = document.getElementById(
      viewName === 'create-job' ? 'viewCreateJob' :
      viewName === 'job-details' ? 'viewJobDetails' :
      viewName === 'preview' ? 'viewPreview' :
      viewName === 'certificates' ? 'viewCertificates' :
      viewName === 'jobs' ? 'viewJobs' : 'viewDashboard'
    );

    if (targetSection) {
      targetSection.classList.add('active');
    }

    // View specific title and data loading
    switch (viewName) {
      case 'dashboard':
        this.pageTitle.textContent = 'Dashboard';
        this.pageSubtitle.textContent = 'High-volume personalized document synthesis and delivery';
        this.loadDashboard();
        break;
      case 'create-job':
        this.pageTitle.textContent = 'Create Generation Job';
        this.pageSubtitle.textContent = 'Configure bulk certificate attributes and recipient roster';
        break;
      case 'jobs':
        this.pageTitle.textContent = 'Generation Jobs';
        this.pageSubtitle.textContent = 'Audit logs and real-time status of all batch processing tasks';
        this.loadJobs();
        break;
      case 'job-details':
        this.pageTitle.textContent = 'Job Progress Monitor';
        this.pageSubtitle.textContent = 'Real-time telemetry, failure isolation and artifact download';
        if (params.jobId) {
          this.activeJobId = params.jobId;
          this.loadJobDetails(this.activeJobId);
        }
        break;
      case 'certificates':
        this.pageTitle.textContent = 'Certificate Vault';
        this.pageSubtitle.textContent = 'Global registry of personalized verifiable credentials';
        this.loadCertificates();
        break;
      case 'preview':
        this.pageTitle.textContent = 'Template Specification';
        this.pageSubtitle.textContent = 'Inspecting live predefined vector layout (Navy, Ivory, Gold)';
        break;
    }
  }

  refreshCurrentView() {
    this.navigateTo(this.currentView, { jobId: this.activeJobId });
    this.showToast('Data refreshed', 'success');
  }

  // Toast System
  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    this.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // Dashboard Data Loading
  async loadDashboard() {
    try {
      const jobsData = await API.getJobs({ limit: 50 });
      const certsData = await API.getCertificates({ limit: 1 }); // to get quick info
      
      const jobs = jobsData.items || [];
      const totalJobs = jobsData.total || 0;

      let totalGenerated = 0;
      let totalInProgress = 0;
      let totalFailed = 0;

      jobs.forEach(j => {
        totalGenerated += j.successful_certificates || 0;
        totalFailed += j.failed_certificates || 0;
        totalInProgress += (j.pending_recipients || 0) + (j.processing_recipients || 0);
      });

      this.kpiTotalJobs.textContent = totalJobs;
      this.kpiTotalGenerated.textContent = totalGenerated;
      this.kpiInProgress.textContent = totalInProgress;
      this.kpiTotalFailed.textContent = totalFailed;

      this.renderDashboardJobsTable(jobs.slice(0, 6));
    } catch (e) {
      this.showToast('Failed to load dashboard metrics: ' + e.message, 'danger');
    }
  }

  renderDashboardJobsTable(jobs) {
    if (!jobs || jobs.length === 0) {
      this.dashboardJobsTbody.innerHTML = `
        <tr>
          <td colspan="7" class="table-empty">No generation jobs found. Click "New Job" to initiate your first bulk certificate batch.</td>
        </tr>
      `;
      return;
    }

    this.dashboardJobsTbody.innerHTML = jobs.map(j => `
      <tr>
        <td><code>${this.escapeHtml(j.id.substring(0, 8))}...</code></td>
        <td><strong>${this.escapeHtml(j.course_name)}</strong></td>
        <td><span class="badge badge-${j.status}">${this.formatStatus(j.status)}</span></td>
        <td>${j.total_recipients}</td>
        <td>
          <div style="min-width: 110px;">
            <div class="progress-bar-container">
              <div class="progress-bar" style="width: ${j.progress_percentage}%"></div>
            </div>
            <span style="font-size: 0.72rem; color: var(--text-muted);">${j.progress_percentage}% (${j.successful_certificates}/${j.total_recipients})</span>
          </div>
        </td>
        <td>${this.formatDate(j.created_at)}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="app.viewJobDetails('${j.id}')">View Details</button>
        </td>
      </tr>
    `).join('');
  }

  // Create Job Roster Management
  setupInitialRecipients() {
    this.recipientsInputTbody.innerHTML = '';
    this.updateRecipientCountDisplay();
  }

  addRecipientRow(name = '', email = '', certId = '') {
    const rowCount = this.recipientsInputTbody.children.length;
    if (rowCount >= 500) {
      this.showToast('Maximum batch size limit (500 recipients) reached.', 'warning');
      return;
    }

    const row = document.createElement('tr');
    const autoCertId = certId || `CERT-2026-${String(rowCount + 1).padStart(3, '0')}`;

    row.innerHTML = `
      <td class="row-num">${rowCount + 1}</td>
      <td>
        <input type="text" class="table-input input-name" placeholder="Full Name" value="${this.escapeHtml(name)}" required>
      </td>
      <td>
        <input type="email" class="table-input input-email" placeholder="name@domain.com" value="${this.escapeHtml(email)}" required>
      </td>
      <td>
        <input type="text" class="table-input input-cert-id" placeholder="CERT-ID" value="${this.escapeHtml(autoCertId)}" required>
      </td>
      <td>
        <button type="button" class="btn-remove-row" title="Remove recipient">&times;</button>
      </td>
    `;

    row.querySelector('.btn-remove-row').addEventListener('click', () => {
      row.remove();
      this.renumberRows();
      this.updateRecipientCountDisplay();
    });

    row.querySelectorAll('input').forEach(input => {
      input.addEventListener('input', () => this.updateRecipientCountDisplay());
    });

    this.recipientsInputTbody.appendChild(row);
    this.updateRecipientCountDisplay();
  }

  renumberRows() {
    const rows = this.recipientsInputTbody.querySelectorAll('tr');
    rows.forEach((row, idx) => {
      const numCell = row.querySelector('.row-num');
      if (numCell) numCell.textContent = idx + 1;
    });
  }

  updateRecipientCountDisplay() {
    const count = this.recipientsInputTbody.children.length;
    this.recipientCountDisplay.innerHTML = `Recipients: <strong>${count}</strong> (Limit: 500)`;
    if (count === 0) {
      this.clientValidationStatus.textContent = '⚠ At least one recipient is required';
      this.clientValidationStatus.style.color = 'var(--danger)';
    } else {
      this.clientValidationStatus.textContent = '✓ Ready for submission';
      this.clientValidationStatus.style.color = 'var(--success)';
    }
  }

  resetCreateJobForm() {
    this.createJobForm.reset();
    this.recipientsInputTbody.innerHTML = '';
    this.updateRecipientCountDisplay();
    this.showToast('Cleared all recipients', 'info');
  }

  downloadSampleCsv() {
    const csvContent = "name,email,certificate_id\n" +
      "Ananya Sharma,ananya@example.com,CERT-2026-001\n" +
      "Rahul Verma,rahul@example.com,CERT-2026-002\n" +
      "Priya Nair,priya.nair@example.com,CERT-2026-003\n" +
      "Vikram Singh,vikram@example.com,CERT-2026-004\n";
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'certiflow_recipients_sample.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    this.showToast('Sample CSV template downloaded', 'success');
  }

  handleCsvUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      this.parseAndLoadCsv(text);
    };
    reader.readAsText(file);
    // Reset input
    event.target.value = '';
  }

  parseAndLoadCsv(csvText) {
    const lines = csvText.split(/\r\n|\n/).filter(line => line.trim() !== '');
    if (lines.length < 2) {
      this.showToast('CSV is empty or lacks data rows', 'danger');
      return;
    }

    // Parse header
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/['"]/g, ''));
    const nameIdx = headers.indexOf('name');
    const emailIdx = headers.indexOf('email');
    const certIdIdx = headers.indexOf('certificate_id') !== -1 ? headers.indexOf('certificate_id') : headers.indexOf('id');

    if (nameIdx === -1 || emailIdx === -1) {
      this.showToast('CSV must include "name" and "email" headers.', 'danger');
      return;
    }

    this.recipientsInputTbody.innerHTML = '';
    let importedCount = 0;

    for (let i = 1; i < lines.length; i++) {
      if (importedCount >= 500) break;
      const cols = lines[i].split(',').map(c => c.trim().replace(/^["']|["']$/g, ''));
      if (cols.length >= 2) {
        const name = cols[nameIdx] || '';
        const email = cols[emailIdx] || '';
        const certId = (certIdIdx !== -1 && cols[certIdIdx]) ? cols[certIdIdx] : `CERT-2026-${String(importedCount + 1).padStart(3, '0')}`;
        this.addRecipientRow(name, email, certId);
        importedCount++;
      }
    }

    this.showToast(`Imported ${importedCount} recipients from CSV successfully`, 'success');
  }

  handleJobFormSubmit(event) {
    event.preventDefault();

    const title = document.getElementById('inputTitle').value.trim();
    const course = document.getElementById('inputCourse').value.trim();
    const org = document.getElementById('inputOrg').value.trim();
    const date = document.getElementById('inputDate').value.trim();
    const signatory = document.getElementById('inputSignatory').value.trim();
    const signatoryTitle = document.getElementById('inputSignatoryTitle').value.trim();

    if (!title || !course || !org || !date || !signatory) {
      this.showToast('Please complete all required certificate fields', 'danger');
      return;
    }

    const rows = this.recipientsInputTbody.querySelectorAll('tr');
    if (rows.length === 0) {
      this.showToast('At least one recipient is required', 'danger');
      return;
    }
    if (rows.length > 500) {
      this.showToast('Batch size exceeds maximum limit of 500 recipients', 'danger');
      return;
    }

    const recipients = [];
    rows.forEach(r => {
      const name = r.querySelector('.input-name').value.trim();
      const email = r.querySelector('.input-email').value.trim();
      const certId = r.querySelector('.input-cert-id').value.trim();
      recipients.push({ name, email, certificate_id: certId });
    });

    this.pendingSubmissionData = {
      certificate: {
        title,
        course_name: course,
        organization_name: org,
        completion_date: date,
        signatory_name: signatory,
        signatory_title: signatoryTitle
      },
      recipients
    };

    // Show Confirmation Modal
    this.modalContent.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:12px;">
        <p>You are about to launch a bulk certificate generation job:</p>
        <div style="background:var(--bg-surface-subtle); padding:14px; border-radius:var(--radius-sm); font-size:0.85rem; border:1px solid var(--border-color);">
          <div><strong>Program:</strong> ${this.escapeHtml(course)}</div>
          <div><strong>Title:</strong> ${this.escapeHtml(title)}</div>
          <div><strong>Organization:</strong> ${this.escapeHtml(org)}</div>
          <div><strong>Issue Date:</strong> ${this.escapeHtml(date)}</div>
          <div><strong>Signatory:</strong> ${this.escapeHtml(signatory)} (${this.escapeHtml(signatoryTitle)})</div>
          <div style="margin-top:6px; color:var(--navy-accent);"><strong>Total Recipients in Batch:</strong> ${recipients.length}</div>
        </div>
        <p style="font-size:0.8rem; color:var(--text-muted);">
          Each recipient will be individually validated and rendered in parallel via background execution. Any individual failures will be isolated without aborting the batch.
        </p>
      </div>
    `;
    this.showModal();
  }

  showModal() {
    this.confirmModal.classList.add('active');
  }

  hideModal() {
    this.confirmModal.classList.remove('active');
  }

  async confirmAndSubmitJob() {
    this.hideModal();
    if (!this.pendingSubmissionData) return;

    const btnSubmit = document.getElementById('btnSubmitJob');
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = 'Submitting & Queuing...';

    try {
      const res = await API.createJob(this.pendingSubmissionData);
      this.showToast(`Job ${res.job_id.substring(0, 8)} created successfully!`, 'success');
      
      // Navigate straight to Job Details to view live progress
      this.viewJobDetails(res.job_id);
    } catch (err) {
      this.showToast('Job creation failed: ' + err.message, 'danger');
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
        Initiate Bulk Generation Job
      `;
    }
  }

  // Jobs List View
  async loadJobs() {
    try {
      const search = this.jobsSearchInput.value.trim();
      const status = this.jobsStatusFilter.value;
      const data = await API.getJobs({ search, status });
      const jobs = data.items || [];

      if (jobs.length === 0) {
        this.jobsListTbody.innerHTML = `
          <tr><td colspan="9" class="table-empty">No generation jobs matched your criteria.</td></tr>
        `;
        return;
      }

      this.jobsListTbody.innerHTML = jobs.map(j => `
        <tr>
          <td><code>${this.escapeHtml(j.id.substring(0, 8))}...</code></td>
          <td><strong>${this.escapeHtml(j.course_name)}</strong><br><small style="color:var(--text-muted)">${this.escapeHtml(j.organization_name)}</small></td>
          <td><span class="badge badge-${j.status}">${this.formatStatus(j.status)}</span></td>
          <td>${j.total_recipients}</td>
          <td style="color:var(--success); font-weight:600;">${j.successful_certificates}</td>
          <td style="color:var(--danger); font-weight:600;">${j.failed_certificates}</td>
          <td>
            <div style="min-width: 100px;">
              <div class="progress-bar-container">
                <div class="progress-bar" style="width: ${j.progress_percentage}%"></div>
              </div>
              <span style="font-size: 0.72rem; color: var(--text-muted);">${j.progress_percentage}%</span>
            </div>
          </td>
          <td>${this.formatDate(j.created_at)}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="app.viewJobDetails('${j.id}')">View</button>
          </td>
        </tr>
      `).join('');
    } catch (e) {
      this.showToast('Failed to load jobs list: ' + e.message, 'danger');
    }
  }

  viewJobDetails(jobId) {
    this.navigateTo('job-details', { jobId });
  }

  // Job Details & Live Polling
  async loadJobDetails(jobId) {
    try {
      const job = await API.getJobDetail(jobId);
      this.renderJobDetailsHeader(job);
      this.loadJobRecipients();

      // Start live polling if job is not terminal
      const isTerminal = ['completed', 'completed_with_errors', 'failed'].includes(job.status);
      if (!isTerminal) {
        this.startPolling(jobId);
      } else {
        this.stopPolling();
        this.jobPollingIndicator.innerHTML = `<span>Generation finished (${this.formatStatus(job.status)})</span>`;
      }
    } catch (err) {
      this.showToast('Failed to fetch job details: ' + err.message, 'danger');
      this.stopPolling();
    }
  }

  renderJobDetailsHeader(job) {
    this.jobDetailId.innerHTML = `Job: <code>${job.id}</code>`;
    this.jobDetailMetaChips.innerHTML = `
      <span class="badge badge-${job.status}">${this.formatStatus(job.status)}</span>
      <span class="chip chip-neutral">${this.escapeHtml(job.course_name)}</span>
      <span class="chip chip-neutral">${this.escapeHtml(job.organization_name)}</span>
      <span class="chip chip-neutral">Issued: ${this.escapeHtml(job.completion_date)}</span>
      <span class="chip chip-neutral">Signatory: ${this.escapeHtml(job.signatory_name)}</span>
    `;

    this.jobDetailProgressPct.textContent = `${job.progress_percentage}%`;
    this.jobDetailProgressBar.style.width = `${job.progress_percentage}%`;

    this.chipCompletedCount.textContent = `Completed: ${job.successful_certificates}`;
    this.chipFailedCount.textContent = `Failed: ${job.failed_certificates}`;
    this.chipProcessingCount.textContent = `Processing: ${job.processing_recipients}`;
    this.chipPendingCount.textContent = `Pending: ${job.pending_recipients}`;

    // ZIP Download button active only if certificates completed
    if (job.successful_certificates > 0) {
      this.btnDownloadJobZip.disabled = false;
    } else {
      this.btnDownloadJobZip.disabled = true;
    }
  }

  async loadJobRecipients() {
    if (!this.activeJobId) return;
    try {
      const search = this.jobRecipientsSearch.value.trim();
      const status = this.jobRecipientsFilter.value;
      const data = await API.getJobRecipients(this.activeJobId, { search, status });
      const recipients = data.items || [];

      if (recipients.length === 0) {
        this.jobRecipientsTbody.innerHTML = `
          <tr><td colspan="6" class="table-empty">No recipient records matched.</td></tr>
        `;
        return;
      }

      this.jobRecipientsTbody.innerHTML = recipients.map(r => `
        <tr>
          <td><strong>${this.escapeHtml(r.recipient_name)}</strong></td>
          <td>${this.escapeHtml(r.recipient_email)}</td>
          <td><code>${this.escapeHtml(r.certificate_id)}</code></td>
          <td><span class="badge badge-${r.status}">${this.formatStatus(r.status)}</span></td>
          <td>
            ${r.error_message ? `<span style="color:var(--danger); font-size:0.78rem;">${this.escapeHtml(r.error_message)}</span>` : '<span style="color:var(--text-light);">-</span>'}
          </td>
          <td>
            ${r.status === 'completed' ? `
              <a href="${API.getCertificateDownloadUrl(r.certificate_id)}" target="_blank" class="btn btn-secondary btn-sm">
                Download PDF
              </a>
            ` : '-'}
          </td>
        </tr>
      `).join('');
    } catch (e) {
      console.error("Failed to load job recipients:", e);
    }
  }

  startPolling(jobId) {
    this.stopPolling();
    this.jobPollingIndicator.style.display = 'inline-flex';
    this.jobPollingIndicator.innerHTML = `
      <div class="pulse-dot"></div>
      <span>Auto-refreshing status...</span>
    `;

    this.pollIntervalId = setInterval(async () => {
      try {
        const job = await API.getJobDetail(jobId);
        this.renderJobDetailsHeader(job);
        this.loadJobRecipients();

        if (['completed', 'completed_with_errors', 'failed'].includes(job.status)) {
          this.stopPolling();
          this.jobPollingIndicator.innerHTML = `<span>Generation finished (${this.formatStatus(job.status)})</span>`;
          this.showToast(`Job ${jobId.substring(0, 8)} has finished processing!`, 'info');
        }
      } catch (e) {
        this.pollFailCount++;
        if (this.pollFailCount > 5) {
          this.stopPolling();
          this.jobPollingIndicator.innerHTML = `<span>Polling halted due to network issues</span>`;
        }
      }
    }, 2500);
  }

  stopPolling() {
    if (this.pollIntervalId) {
      clearInterval(this.pollIntervalId);
      this.pollIntervalId = null;
    }
    this.pollFailCount = 0;
  }

  // Certificate Vault View
  async loadCertificates() {
    try {
      const search = this.certSearchInput.value.trim();
      const status = this.certStatusFilter.value;
      const certs = await API.getCertificates({ search, status });

      if (!certs || certs.length === 0) {
        this.certificatesListTbody.innerHTML = `
          <tr><td colspan="7" class="table-empty">No certificates recorded in vault.</td></tr>
        `;
        return;
      }

      this.certificatesListTbody.innerHTML = certs.map(c => `
        <tr>
          <td><code>${this.escapeHtml(c.certificate_id)}</code></td>
          <td><strong>${this.escapeHtml(c.recipient_name)}</strong></td>
          <td>${this.escapeHtml(c.recipient_email)}</td>
          <td>${this.escapeHtml(c.course_name)}</td>
          <td><span class="badge badge-${c.status}">${this.formatStatus(c.status)}</span></td>
          <td>${this.escapeHtml(c.completion_date)}</td>
          <td>
            ${c.status === 'completed' ? `
              <a href="${API.getCertificateDownloadUrl(c.certificate_id)}" target="_blank" class="btn btn-secondary btn-sm">
                Download PDF
              </a>
            ` : `<span style="font-size:0.75rem; color:var(--danger)">Unavailable</span>`}
          </td>
        </tr>
      `).join('');
    } catch (e) {
      this.showToast('Failed to load certificates: ' + e.message, 'danger');
    }
  }

  // Formatters & Utilities
  formatStatus(status) {
    if (!status) return 'Unknown';
    return status.replace(/_/g, ' ');
  }

  formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return dateStr;
    }
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
}

// Global instance
let app;
document.addEventListener('DOMContentLoaded', () => {
  app = new CertiFlowApp();
});
