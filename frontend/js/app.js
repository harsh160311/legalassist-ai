/**
 * LegalAssist AI - Frontend JavaScript
 * Handles API calls, UI interactions, and state management
 */

// API Base URL
const API_BASE = '';

// State Management
const state = {
    currentDocument: null,
    comparisonDocuments: { a: null, b: null },
    chatHistory: [],
    analysisResults: null
};

// ============================================
// API Helper Functions
// ============================================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || `HTTP error ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function uploadFile(file, endpoint) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(error.detail || `Upload failed`);
    }
    
    return await response.json();
}

// ============================================
// UI Helper Functions
// ============================================

function showLoading(message = 'Processing...') {
    const existing = document.getElementById('loading-overlay');
    if (existing) existing.remove();
    
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-spinner loading-spinner-lg"></div>
        <div class="loading-text">${message}</div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.remove();
}

function showAlert(message, type = 'info', duration = 5000) {
    const container = document.getElementById('alerts-container') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span class="alert-icon">${getAlertIcon(type)}</span>
        <span>${message}</span>
    `;
    
    container.appendChild(alert);
    
    if (duration > 0) {
        setTimeout(() => alert.remove(), duration);
    }
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alerts-container';
    container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 1000; max-width: 400px;';
    document.body.appendChild(container);
    return container;
}

function getAlertIcon(type) {
    const icons = {
        success: '✓',
        warning: '⚠',
        danger: '✕',
        info: 'ℹ'
    };
    return icons[type] || icons.info;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ============================================
// Navigation
// ============================================

function initNavigation() {
    const toggle = document.querySelector('.nav-mobile-toggle');
    const links = document.querySelector('.nav-links');
    
    if (toggle && links) {
        toggle.addEventListener('click', () => {
            links.classList.toggle('active');
        });
    }
    
    // Set active link based on current path
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-links a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// ============================================
// Dashboard Functions
// ============================================

async function loadDashboard() {
    try {
        const response = await apiCall('/api/status');
        updateDashboardStats(response);
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

function updateDashboardStats(status) {
    const geminiStatus = document.getElementById('gemini-status');
    if (geminiStatus) {
        geminiStatus.textContent = status.gemini_configured ? 'Connected' : 'Not Configured';
        geminiStatus.className = status.gemini_configured ? 'badge badge-success' : 'badge badge-danger';
    }
}

// ============================================
// Document Upload & Analysis
// ============================================

function initUploadZone() {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    
    if (!uploadZone || !fileInput) return;
    
    // Click to upload
    uploadZone.addEventListener('click', () => fileInput.click());
    
    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

async function handleFileSelect(file) {
    // Validate file type
    const validTypes = ['.pdf', '.docx', '.doc', '.txt'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExt)) {
        showAlert('Invalid file type. Please upload PDF, DOCX, or TXT files.', 'danger');
        return;
    }
    
    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
        showAlert('File too large. Maximum size is 10MB.', 'danger');
        return;
    }
    
    showLoading('Uploading document...');
    
    try {
        const result = await uploadFile(file, '/api/documents/upload');
        
        if (result.success) {
            state.currentDocument = {
                id: result.document_id,
                filename: result.filename,
                type: result.file_type,
                size: result.file_size
            };
            
            showAlert('Document uploaded successfully!', 'success');
            updateFileInfo(result);
            showAnalysisButton();
        } else {
            throw new Error(result.message || 'Upload failed');
        }
    } catch (error) {
        showAlert(`Upload failed: ${error.message}`, 'danger');
    } finally {
        hideLoading();
    }
}

function updateFileInfo(result) {
    const fileInfo = document.getElementById('file-info');
    if (fileInfo) {
        fileInfo.innerHTML = `
            <div class="file-info">
                <div class="file-icon">${getFileIcon(result.file_type)}</div>
                <div class="file-details">
                    <div class="file-name">${result.filename}</div>
                    <div class="file-meta">${formatFileSize(result.file_size)} • ${result.file_type.toUpperCase()}</div>
                </div>
                <span class="badge badge-success">Uploaded</span>
            </div>
        `;
        fileInfo.classList.remove('hidden');
    }
}

function getFileIcon(type) {
    const icons = {
        '.pdf': '<span class="icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg></span>',
        '.docx': '<span class="icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg></span>',
        '.doc': '<span class="icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg></span>',
        '.txt': '<span class="icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg></span>'
    };
    return icons[type] || '<span class="icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg></span>';
}

function showAnalysisButton() {
    const analyzeBtn = document.getElementById('analyze-btn');
    if (analyzeBtn) {
        analyzeBtn.classList.remove('hidden');
    }
}

async function analyzeDocument() {
    if (!state.currentDocument) {
        showAlert('Please upload a document first.', 'warning');
        return;
    }
    
    showLoading('Analyzing document with AI...');
    
    try {
        const response = await fetch(`${API_BASE}/api/documents/${state.currentDocument.id}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (!response.ok || !result.success) {
            const errMsg = result.error?.message || result.detail || `HTTP ${response.status}`;
            throw new Error(errMsg);
        }
        
        state.analysisResults = result.analysis;
        showAlert('Document analyzed successfully!', 'success');
        displayAnalysisResults(result.analysis);
    } catch (error) {
        showAlert(`Analysis failed: ${error.message}`, 'danger');
    } finally {
        hideLoading();
    }
}

function displayAnalysisResults(analysis) {
    const resultsContainer = document.getElementById('analysis-results');
    if (!resultsContainer) return;

    const hasFinancial = analysis.financial_terms && Object.values(analysis.financial_terms).some(v => Array.isArray(v) ? v.length > 0 : v);
    const hasTermination = analysis.termination_terms && analysis.termination_terms.notice_period;
    const hasLiability = analysis.liability_terms && (analysis.liability_terms.liability_cap || analysis.liability_terms.indemnification);
    const hasDispute = analysis.dispute_resolution && analysis.dispute_resolution.method;
    const hasObligations = analysis.obligations && analysis.obligations.length > 0;

    resultsContainer.innerHTML = `
        ${renderTrustBanner(analysis)}
        ${renderDocumentOverview(analysis)}
        ${renderExtractedFacts(analysis)}
        ${renderParties(analysis.parties)}
        ${hasObligations ? renderObligations(analysis.obligations) : ''}
        ${renderImportantClauses(analysis.important_clauses)}
        ${renderRisks(analysis.risks)}
        ${renderMissingInfo(analysis.missing_information)}
        ${hasFinancial ? renderFinancialTerms(analysis.financial_terms) : ''}
        ${hasTermination ? renderTerminationTerms(analysis.termination_terms) : ''}
        ${hasLiability ? renderLiabilityTerms(analysis.liability_terms) : ''}
        ${hasDispute ? renderDisputeResolution(analysis.dispute_resolution) : ''}
        ${renderActionChecklist(analysis.action_checklist)}
        ${renderLawyerQuestions(analysis.lawyer_questions)}
    `;

    resultsContainer.classList.remove('hidden');
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

function renderTrustBanner(analysis) {
    const trust = analysis.trust_indicators || {};
    const hasSensitive = analysis.has_sensitive_data || trust.has_sensitive_data;
    const requiresVerification = trust.requires_verification || [];

    let html = '<div class="trust-banner">';

    if (hasSensitive) {
        html += '<div class="trust-item trust-sensitive"><span class="icon icon-sm"><svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg></span> Sensitive information detected. Identifiers are masked in the analysis view.</div>';
    }

    if (requiresVerification.length > 0) {
        html += `<div class="trust-item trust-verify"><span class="icon icon-sm"><svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span> Items requiring professional verification: ${requiresVerification.join(', ')}</div>`;
    }

    html += '<div class="trust-item trust-ai">AI analysis is generated from the uploaded document. Review sensitive information before sharing or exporting this report.</div>';
    html += '</div>';

    return html;
}

function renderDocumentOverview(analysis) {
    const overview = analysis.document_overview;
    if (!overview) {
        return `
            <div class="analysis-section">
                <h3 class="analysis-section-title"><span class="icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg></span> Document Overview</h3>
                <div class="card"><div class="card-body">
                    <div class="badge badge-info mb-2">${analysis.document_type || 'Legal Document'}</div>
                    <p style="white-space: pre-line;">${analysis.summary || 'No summary available.'}</p>
                </div></div>
            </div>
        `;
    }

    const parties = (overview.key_authorities || []).map(a => `<span class="badge badge-neutral">${a}</span>`).join(' ');
    const dates = (overview.key_dates || []).join(', ');

    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title"><span class="icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg></span> Document Overview</h3>
            <div class="card">
                <div class="card-body">
                    <div class="overview-grid">
                        <div class="overview-row">
                            <div class="overview-label">Document Type</div>
                            <div class="overview-value"><span class="badge badge-info">${overview.type || analysis.document_type || 'Unknown'}</span></div>
                        </div>
                        <div class="overview-row">
                            <div class="overview-label">Purpose</div>
                            <div class="overview-value">${overview.purpose || 'Not determined'}</div>
                        </div>
                        ${overview.key_subject ? `
                        <div class="overview-row">
                            <div class="overview-label">Key Subject</div>
                            <div class="overview-value">${overview.key_subject}</div>
                        </div>` : ''}
                        ${parties ? `
                        <div class="overview-row">
                            <div class="overview-label">Key Authorities</div>
                            <div class="overview-value">${parties}</div>
                        </div>` : ''}
                        ${dates ? `
                        <div class="overview-row">
                            <div class="overview-label">Key Dates</div>
                            <div class="overview-value">${dates}</div>
                        </div>` : ''}
                    </div>
                    <div class="mt-3">
                        <strong>Summary:</strong>
                        <p style="white-space: pre-line; margin-top: 0.5rem;">${analysis.summary || 'No summary available.'}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderExtractedFacts(analysis) {
    const facts = analysis.extracted_facts;
    if (!facts) return '';

    const sections = [];

    if (facts.identification_details && facts.identification_details.length > 0) {
        sections.push(renderFactGroup('Identification Details', facts.identification_details));
    }
    if (facts.tax_identifiers && facts.tax_identifiers.length > 0) {
        sections.push(renderFactGroup('Tax Identifiers', facts.tax_identifiers));
    }
    if (facts.treaty_information && facts.treaty_information.length > 0) {
        sections.push(renderFactGroup('Treaty Information', facts.treaty_information));
    }
    if (facts.amounts && facts.amounts.length > 0) {
        sections.push(renderFactGroup('Financial Amounts', facts.amounts));
    }
    if (facts.dates && facts.dates.length > 0) {
        sections.push(renderFactGroup('Key Dates', facts.dates));
    }
    if (facts.addresses && facts.addresses.length > 0) {
        sections.push(renderFactGroup('Addresses', facts.addresses));
    }
    if (facts.important_fields && facts.important_fields.length > 0) {
        sections.push(renderFactGroup('Other Important Fields', facts.important_fields));
    }

    if (sections.length === 0) return '';

    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>📌</span> Extracted Information
                <span class="trust-indicator">Extracted from document</span>
            </h3>
            <div class="card">
                <div class="card-body">
                    <div class="extracted-facts-grid">
                        ${sections.join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderFactGroup(title, facts) {
    if (!facts || facts.length === 0) return '';

    const rows = facts.map(f => {
        const displayValue = f.value_display || f.value || 'Not specified';
        const source = f.source || '';
        const page = f.page ? ` (p.${f.page})` : '';
        const sensitiveTag = f.sensitive ? ' <span class="badge badge-warning" style="font-size:0.65rem;">SENSITIVE</span>' : '';
        const confidenceTag = f.confidence !== undefined && f.confidence < 0.9 ? ` <span class="text-muted" style="font-size:0.75rem;">(${Math.round(f.confidence*100)}% confidence)</span>` : '';

        return `
            <div class="fact-row">
                <div class="fact-field">${f.field || 'Unknown'}${sensitiveTag}</div>
                <div class="fact-value">${displayValue}${confidenceTag}</div>
                <div class="fact-source">${source}${page}</div>
            </div>
        `;
    }).join('');

    return `
        <div class="fact-group">
            <h4 class="fact-group-title">${title}</h4>
            ${rows}
        </div>
    `;
}

function renderParties(parties) {
    if (!parties || parties.length === 0) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span class="icon"><svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg></span> Involved Parties
            </h3>
            <div class="card">
                <div class="card-body">
                    ${parties.map(party => `
                        <div class="clause-card">
                            <div class="clause-card-header">
                                <div class="clause-card-title">${party.name}</div>
                                <span class="badge badge-neutral">${party.role}</span>
                            </div>
                            ${party.obligations && party.obligations.length > 0 ? `
                                <div class="clause-card-content">
                                    <strong>Key Obligations:</strong>
                                    <ul style="margin-top: 0.5rem; margin-left: 1.5rem;">
                                        ${party.obligations.map(o => `<li>${o}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

function renderObligations(obligations) {
    if (!obligations || obligations.length === 0) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>⚖️</span> Key Obligations
            </h3>
            <div class="card">
                <div class="table-wrapper">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Party</th>
                                <th>Obligation</th>
                                <th>Deadline</th>
                                <th>Consequence</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${obligations.map(o => `
                                <tr>
                                    <td><strong>${o.party || 'N/A'}</strong></td>
                                    <td>${o.obligation || 'N/A'}</td>
                                    <td>${o.deadline || 'Not specified'}</td>
                                    <td>${o.consequence || 'Not specified'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

function renderImportantClauses(clauses) {
    if (!clauses || clauses.length === 0) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>📑</span> Important Clauses
            </h3>
            ${clauses.map(clause => `
                <div class="clause-card">
                    <div class="clause-card-header">
                        <div class="clause-card-title">${clause.clause_name}</div>
                        ${clause.location ? `<span class="badge badge-neutral">${clause.location}</span>` : ''}
                    </div>
                    <div class="clause-card-content">
                        <p><strong>Summary:</strong> ${clause.summary}</p>
                        <p><strong>Significance:</strong> ${clause.significance}</p>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderRisks(risks) {
    if (!risks || risks.length === 0) return '';

    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span class="icon"><svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span> Potential Concerns & Risks
            </h3>
            ${risks.map(risk => {
                const typeLabel = risk.type === 'LEGAL_CONCERN' ? '<span class="badge badge-danger" style="font-size:0.65rem;">LEGAL CONCERN — Requires verification</span>'
                    : risk.type === 'POTENTIAL_CONCERN' ? '<span class="badge badge-warning" style="font-size:0.65rem;">POTENTIAL CONCERN</span>'
                    : '<span class="badge badge-neutral" style="font-size:0.65rem;">DOCUMENT FACT</span>';
                const confidenceTag = risk.confidence !== undefined ? ` <span class="text-muted" style="font-size:0.75rem;">(${Math.round(risk.confidence*100)}%)</span>` : '';

                return `
                <div class="risk-item">
                    <div class="risk-item-indicator ${risk.level?.toLowerCase() || 'low'}"></div>
                    <div class="risk-item-content">
                        <div class="risk-item-header">
                            <div class="risk-item-title">${risk.title || risk.clause || 'Risk'}</div>
                            <div>
                                ${typeLabel}
                                <span class="risk-badge risk-${risk.level?.toLowerCase() || 'low'}">${risk.level || 'LOW'}</span>
                            </div>
                        </div>
                        ${risk.fact ? `<div class="risk-item-description"><strong>Observation:</strong> ${risk.fact}</div>` : ''}
                        <div class="risk-item-description">${risk.explanation || ''}</div>
                        <div class="risk-item-description"><strong>Why it matters:</strong> ${risk.why_it_matters || ''}</div>
                        <div class="risk-item-action"><span class="icon icon-sm"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg></span> Consider: ${risk.suggested_action || 'Review with a qualified professional'}</div>
                        <div class="trust-indicator-inline">Trust: ${typeLabel} ${confidenceTag} ${risk.source ? `• Source: ${risk.source}` : ''}</div>
                    </div>
                </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderMissingInfo(missing) {
    if (!missing || missing.length === 0) return '';

    const required = missing.filter(m => (m.importance || 'REQUIRED') === 'REQUIRED');
    const contextual = missing.filter(m => m.importance === 'CONTEXTUAL');

    if (required.length === 0 && contextual.length === 0) return '';

    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>❓</span> Missing / Unclear Information
            </h3>
            <div class="card">
                <div class="card-body">
                    ${required.length > 0 ? `
                        <div class="mb-3">
                            <strong class="text-danger">Required / Important:</strong>
                            <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                                ${required.map(item => `<li><strong>${item.field || item}</strong>${item.reason ? ` — ${item.reason}` : ''}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${contextual.length > 0 ? `
                        <div>
                            <strong class="text-muted">Contextual (would improve understanding):</strong>
                            <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                                ${contextual.map(item => `<li><strong>${item.field || item}</strong>${item.reason ? ` — ${item.reason}` : ''}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderFinancialTerms(terms) {
    if (!terms) return '';
    
    const hasContent = terms.payment_amounts?.length || 
                      terms.payment_schedule?.length || 
                      terms.penalties?.length ||
                      terms.other_financial?.length;
    
    if (!hasContent) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>💰</span> Financial Terms
            </h3>
            <div class="card">
                <div class="card-body">
                    ${terms.payment_amounts?.length ? `
                        <div class="mb-2">
                            <strong>Payment Amounts:</strong>
                            <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                                ${terms.payment_amounts.map(p => `<li>${p}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${terms.payment_schedule?.length ? `
                        <div class="mb-2">
                            <strong>Payment Schedule:</strong>
                            <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                                ${terms.payment_schedule.map(p => `<li>${p}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${terms.penalties?.length ? `
                        <div class="mb-2">
                            <strong>Penalties:</strong>
                            <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                                ${terms.penalties.map(p => `<li>${p}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderTerminationTerms(terms) {
    if (!terms) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>🚪</span> Termination Terms
            </h3>
            <div class="card">
                <div class="card-body">
                    <p><strong>Notice Period:</strong> ${terms.notice_period || 'Not specified'}</p>
                    ${terms.conditions?.length ? `
                        <p><strong>Conditions:</strong></p>
                        <ul style="margin-left: 1.5rem;">
                            ${terms.conditions.map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    ` : ''}
                    ${terms.consequences?.length ? `
                        <p><strong>Consequences:</strong></p>
                        <ul style="margin-left: 1.5rem;">
                            ${terms.consequences.map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderLiabilityTerms(terms) {
    if (!terms) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span class="icon"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></span> Liability Terms
            </h3>
            <div class="card">
                <div class="card-body">
                    <p><strong>Liability Cap:</strong> ${terms.liability_cap || 'Not specified'}</p>
                    ${terms.exclusions?.length ? `
                        <p><strong>Exclusions:</strong></p>
                        <ul style="margin-left: 1.5rem;">
                            ${terms.exclusions.map(e => `<li>${e}</li>`).join('')}
                        </ul>
                    ` : ''}
                    ${terms.indemnification ? `
                        <p><strong>Indemnification:</strong> ${terms.indemnification}</p>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderDisputeResolution(terms) {
    if (!terms) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>🏛️</span> Dispute Resolution
            </h3>
            <div class="card">
                <div class="card-body">
                    <p><strong>Method:</strong> ${terms.method || 'Not specified'}</p>
                    <p><strong>Jurisdiction:</strong> ${terms.jurisdiction || 'Not specified'}</p>
                    <p><strong>Venue:</strong> ${terms.venue || 'Not specified'}</p>
                </div>
            </div>
        </div>
    `;
}

function renderLawyerQuestions(questions) {
    if (!questions || questions.length === 0) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span class="icon"><svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span> Questions to Ask a Lawyer
            </h3>
            <div class="card">
                <div class="card-body">
                    <ol style="margin-left: 1.5rem;">
                        ${questions.map(q => `<li style="margin-bottom: 0.5rem;">${q}</li>`).join('')}
                    </ol>
                </div>
            </div>
        </div>
    `;
}

function renderActionChecklist(checklist) {
    if (!checklist || checklist.length === 0) return '';

    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span class="icon"><svg viewBox="0 0 24 24"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg></span> Action Checklist
                <span class="trust-indicator">Advisory — not legal advice</span>
            </h3>
            <div class="card">
                <ul class="checklist">
                    ${checklist.map((item, index) => `
                        <li class="checklist-item">
                            <div class="checklist-checkbox" onclick="toggleChecklistItem(this)"></div>
                            <div class="checklist-content">
                                <div class="checklist-text">${item.action}</div>
                                <div class="checklist-meta">
                                    <span class="badge badge-${item.priority?.toLowerCase() === 'high' ? 'danger' : item.priority?.toLowerCase() === 'medium' ? 'warning' : 'neutral'}">${item.priority || 'LOW'}</span>
                                    ${item.reason ? ` — ${item.reason}` : ''}
                                </div>
                                ${item.source ? `<div class="trust-indicator-inline">Source: ${item.source}</div>` : ''}
                            </div>
                        </li>
                    `).join('')}
                </ul>
            </div>
        </div>
    `;
}

function toggleChecklistItem(element) {
    element.classList.toggle('checked');
    if (element.classList.contains('checked')) {
        element.innerHTML = '✓';
    } else {
        element.innerHTML = '';
    }
}

// ============================================
// Document Q&A
// ============================================

async function sendQuestion() {
    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    
    if (!question) return;
    
    if (!state.currentDocument) {
        showAlert('Please upload a document first.', 'warning');
        return;
    }
    
    // Add user message to chat
    addChatMessage(question, 'user');
    input.value = '';
    
    showLoading('Thinking...');
    
    try {
        const result = await apiCall('/api/chat/ask', {
            method: 'POST',
            body: JSON.stringify({
                document_id: state.currentDocument.id,
                question: question,
                chat_history: state.chatHistory.slice(-10) // Last 10 messages for context
            })
        });
        
        if (result.success) {
            const answer = result.answer;
            addChatMessage(formatAnswer(answer), 'assistant');
            
            // Update chat history
            state.chatHistory.push(
                { role: 'user', content: question },
                { role: 'assistant', content: answer.answer }
            );
        } else {
            throw new Error('Failed to get answer');
        }
    } catch (error) {
        addChatMessage(`Sorry, I couldn't process your question: ${error.message}`, 'assistant');
    } finally {
        hideLoading();
    }
}

function addChatMessage(content, role) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    messageDiv.innerHTML = `
        <div class="chat-avatar">${role === 'user' ? 'You' : 'AI'}</div>
        <div class="chat-bubble">${content}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatAnswer(answer) {
    let html = `<p>${answer.answer || 'No answer available.'}</p>`;
    
    if (answer.sources && answer.sources.length > 0) {
        html += `<div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(255,255,255,0.2);">`;
        html += `<strong>Sources:</strong><ul style="margin-left: 1.5rem; margin-top: 0.5rem;">`;
        answer.sources.forEach(source => {
            html += `<li>${source.section || 'Document'}${source.page ? ` (Page ${source.page})` : ''}</li>`;
        });
        html += `</ul></div>`;
    }
    
    if (answer.follow_up_questions && answer.follow_up_questions.length > 0) {
        html += `<div style="margin-top: 0.75rem; font-size: 0.875rem; opacity: 0.9;">`;
        html += `<strong>Follow-up questions:</strong> ${answer.follow_up_questions.join(' • ')}`;
        html += `</div>`;
    }
    
    return html;
}

// ============================================
// Document Comparison
// ============================================

async function loadDocumentsForComparison() {
    try {
        const documents = await apiCall('/api/compare/documents');
        updateDocumentSelects(documents);
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

function updateDocumentSelects(documents) {
    const selectA = document.getElementById('doc-a-select');
    const selectB = document.getElementById('doc-b-select');
    
    const options = documents.map(doc => 
        `<option value="${doc.document_id}">${doc.filename}</option>`
    ).join('');
    
    const defaultOption = '<option value="">Select a document...</option>';
    
    if (selectA) selectA.innerHTML = defaultOption + options;
    if (selectB) selectB.innerHTML = defaultOption + options;
}

async function compareDocuments() {
    const docAId = document.getElementById('doc-a-select')?.value;
    const docBId = document.getElementById('doc-b-select')?.value;
    
    if (!docAId || !docBId) {
        showAlert('Please select both documents to compare.', 'warning');
        return;
    }
    
    if (docAId === docBId) {
        showAlert('Please select two different documents.', 'warning');
        return;
    }
    
    showLoading('Comparing documents...');
    
    try {
        const result = await apiCall('/api/compare/', {
            method: 'POST',
            body: JSON.stringify({
                document_a_id: docAId,
                document_b_id: docBId
            })
        });
        
        if (result.success) {
            displayComparisonResults(result.comparison);
        } else {
            throw new Error('Comparison failed');
        }
    } catch (error) {
        showAlert(`Comparison failed: ${error.message}`, 'danger');
    } finally {
        hideLoading();
    }
}

function displayComparisonResults(comparison) {
    const resultsContainer = document.getElementById('comparison-results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>📊</span> Comparison Summary
            </h3>
            <div class="card">
                <div class="card-body">
                    <p style="white-space: pre-line;">${comparison.summary || 'No summary available.'}</p>
                </div>
            </div>
        </div>
        
        ${renderKeyDifferences(comparison.key_differences)}
        ${renderChangedClauses(comparison.changed_clauses)}
        ${renderAddedClauses(comparison.added_in_b)}
        ${renderRemovedClauses(comparison.removed_from_a)}
        ${renderComparisonSection('Payment Terms', comparison.payment_terms_comparison)}
        ${renderComparisonSection('Termination', comparison.termination_comparison)}
        ${renderComparisonSection('Liability', comparison.liability_comparison)}
        ${renderComparisonSection('Jurisdiction', comparison.jurisdiction_comparison)}
        
        ${comparison.recommendations?.length ? `
            <div class="analysis-section">
                <h3 class="analysis-section-title">
                    <span class="icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg></span> Recommendations
                </h3>
                <div class="card">
                    <div class="card-body">
                        <ul style="margin-left: 1.5rem;">
                            ${comparison.recommendations.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        ` : ''}
    `;
    
    resultsContainer.classList.remove('hidden');
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

function renderKeyDifferences(differences) {
    if (!differences || differences.length === 0) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span class="icon"><svg viewBox="0 0 24 24"><path d="M16 3h5v5M8 3H3v5M3 16v5h5M21 16v5h-5"/><line x1="3" y1="12" x2="21" y2="12"/></svg></span> Key Differences
            </h3>
            <div class="card">
                <div class="table-wrapper">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Category</th>
                                <th>Document A</th>
                                <th>Document B</th>
                                <th>Significance</th>
                                <th>Risk</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${differences.map(d => `
                                <tr>
                                    <td><strong>${d.category || 'N/A'}</strong></td>
                                    <td>${d.document_a || 'N/A'}</td>
                                    <td>${d.document_b || 'N/A'}</td>
                                    <td>${d.significance || 'N/A'}</td>
                                    <td><span class="risk-badge risk-${d.risk_level?.toLowerCase() || 'low'}">${d.risk_level || 'LOW'}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

function renderChangedClauses(clauses) {
    if (!clauses || clauses.length === 0) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span class="icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg></span> Changed Clauses
            </h3>
            ${clauses.map(clause => `
                <div class="clause-card">
                    <div class="clause-card-header">
                        <div class="clause-card-title">${clause.clause_name}</div>
                    </div>
                    <div class="clause-card-content">
                        <p><strong>In Document A:</strong> ${clause.in_document_a}</p>
                        <p><strong>In Document B:</strong> ${clause.in_document_b}</p>
                        <p><strong>Impact:</strong> ${clause.impact}</p>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderAddedClauses(clauses) {
    if (!clauses || clauses.length === 0) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>➕</span> Added in Document B
            </h3>
            ${clauses.map(clause => `
                <div class="clause-card" style="border-left: 3px solid var(--success-color);">
                    <div class="clause-card-header">
                        <div class="clause-card-title">${clause.clause_name}</div>
                        <span class="badge badge-success">New</span>
                    </div>
                    <div class="clause-card-content">
                        <p>${clause.description}</p>
                        <p><strong>Significance:</strong> ${clause.significance}</p>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderRemovedClauses(clauses) {
    if (!clauses || clauses.length === 0) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>➖</span> Removed from Document A
            </h3>
            ${clauses.map(clause => `
                <div class="clause-card" style="border-left: 3px solid var(--danger-color);">
                    <div class="clause-card-header">
                        <div class="clause-card-title">${clause.clause_name}</div>
                        <span class="badge badge-danger">Removed</span>
                    </div>
                    <div class="clause-card-content">
                        <p>${clause.description}</p>
                        <p><strong>Impact:</strong> ${clause.impact}</p>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderComparisonSection(title, section) {
    if (!section) return '';
    
    return `
        <div class="analysis-section">
            <h3 class="analysis-section-title">
                <span>📋</span> ${title} Comparison
            </h3>
            <div class="card">
                <div class="card-body">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                        <div>
                            <strong>Document A:</strong>
                            <p style="margin-top: 0.5rem;">${section.document_a || 'Not specified'}</p>
                        </div>
                        <div>
                            <strong>Document B:</strong>
                            <p style="margin-top: 0.5rem;">${section.document_b || 'Not specified'}</p>
                        </div>
                    </div>
                    ${section.differences ? `
                        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-light);">
                            <strong>Key Differences:</strong>
                            <p style="margin-top: 0.5rem;">${section.differences}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// ============================================
// Clause Explainer
// ============================================

async function explainClause() {
    const clauseInput = document.getElementById('clause-input');
    const clauseText = clauseInput?.value.trim();
    
    if (!clauseText) {
        showAlert('Please enter a clause to explain.', 'warning');
        return;
    }
    
    showLoading('Explaining clause...');
    
    try {
        const result = await apiCall('/api/chat/explain-clause', {
            method: 'POST',
            body: JSON.stringify({
                clause_text: clauseText,
                document_id: state.currentDocument?.id || null
            })
        });
        
        if (result.success) {
            displayClauseExplanation(result.explanation);
        } else {
            throw new Error('Explanation failed');
        }
    } catch (error) {
        showAlert(`Explanation failed: ${error.message}`, 'danger');
    } finally {
        hideLoading();
    }
}

function displayClauseExplanation(explanation) {
    const container = document.getElementById('clause-explanation');
    if (!container) return;
    
    container.innerHTML = `
        <div class="card mt-3">
            <div class="card-header">
                <h4 style="margin: 0;">Explanation</h4>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <strong>Simple Explanation:</strong>
                    <p style="margin-top: 0.5rem; white-space: pre-line;">${explanation.simple_explanation || 'No explanation available.'}</p>
                </div>
                
                ${explanation.key_points?.length ? `
                    <div class="mb-3">
                        <strong>Key Points:</strong>
                        <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                            ${explanation.key_points.map(p => `<li>${p}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${explanation.implications?.length ? `
                    <div class="mb-3">
                        <strong>Implications:</strong>
                        <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                            ${explanation.implications.map(i => `<li>${i}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${explanation.potential_concerns?.length ? `
                    <div class="mb-3">
                        <strong>Potential Concerns:</strong>
                        <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                            ${explanation.potential_concerns.map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${explanation.questions_to_ask?.length ? `
                    <div>
                        <strong>Questions to Ask:</strong>
                        <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                            ${explanation.questions_to_ask.map(q => `<li>${q}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    container.classList.remove('hidden');
}

// ============================================
// Compare Page Upload
// ============================================

function initCompareUploadZones() {
    setupUploadZone('upload-zone-a', 'file-input-a', 'file-info-a', 'a');
    setupUploadZone('upload-zone-b', 'file-input-b', 'file-info-b', 'b');
}

function setupUploadZone(zoneId, inputId, infoId, slot) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    
    if (!zone || !input) return;
    
    zone.addEventListener('click', () => input.click());
    
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });
    
    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });
    
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleCompareFileSelect(e.dataTransfer.files[0], slot, infoId);
        }
    });
    
    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleCompareFileSelect(e.target.files[0], slot, infoId);
        }
    });
}

async function handleCompareFileSelect(file, slot, infoId) {
    const validTypes = ['.pdf', '.docx', '.doc', '.txt'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExt)) {
        showAlert('Invalid file type. Please upload PDF, DOCX, or TXT files.', 'danger');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showAlert('File too large. Maximum size is 10MB.', 'danger');
        return;
    }
    
    showLoading('Uploading document...');
    
    try {
        const result = await uploadFile(file, '/api/documents/upload');
        
        if (result.success) {
            state.comparisonDocuments[slot] = {
                id: result.document_id,
                filename: result.filename,
                type: result.file_type,
                size: result.file_size
            };
            
            const infoEl = document.getElementById(infoId);
            if (infoEl) {
                infoEl.innerHTML = `
                    <div class="file-info" style="margin: 0; padding: 0.75rem;">
                        <div class="file-icon" style="width: 36px; height: 36px; font-size: 1rem;">${getFileIcon(result.file_type)}</div>
                        <div class="file-details">
                            <div class="file-name" style="font-size: 0.9rem;">${result.filename}</div>
                            <div class="file-meta">${formatFileSize(result.file_size)}</div>
                        </div>
                        <span class="badge badge-success" style="font-size: 0.65rem;">Uploaded</span>
                    </div>
                `;
                infoEl.classList.remove('hidden');
            }
            
            showAlert(`Document ${slot.toUpperCase()} uploaded successfully!`, 'success');
            loadDocumentsForComparison();
        } else {
            throw new Error(result.message || 'Upload failed');
        }
    } catch (error) {
        showAlert(`Upload failed: ${error.message}`, 'danger');
    } finally {
        hideLoading();
    }
}

// ============================================
// Chat Page Upload
// ============================================

function initChatUploadZone() {
    const zone = document.getElementById('upload-zone-chat');
    const input = document.getElementById('file-input-chat');
    
    if (!zone || !input) return;
    
    zone.addEventListener('click', () => input.click());
    
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });
    
    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });
    
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleChatFileSelect(e.dataTransfer.files[0]);
        }
    });
    
    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleChatFileSelect(e.target.files[0]);
        }
    });
}

async function handleChatFileSelect(file) {
    const validTypes = ['.pdf', '.docx', '.doc', '.txt'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExt)) {
        showAlert('Invalid file type. Please upload PDF, DOCX, or TXT files.', 'danger');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showAlert('File too large. Maximum size is 10MB.', 'danger');
        return;
    }
    
    showLoading('Uploading document...');
    
    try {
        const result = await uploadFile(file, '/api/documents/upload');
        
        if (result.success) {
            state.currentDocument = {
                id: result.document_id,
                filename: result.filename,
                type: result.file_type,
                size: result.file_size
            };
            
            document.getElementById('no-document-warning').style.display = 'none';
            
            const docInfo = document.getElementById('current-doc-info');
            if (docInfo) {
                docInfo.innerHTML = `
                    <div class="file-info" style="margin: 0;">
                        <div class="file-icon"><span class="icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg></span></div>
                        <div class="file-details">
                            <div class="file-name">${result.filename}</div>
                            <div class="file-meta">${result.file_type.toUpperCase()}</div>
                        </div>
                    </div>
                `;
            }
            
            showAlert('Document uploaded successfully! You can now ask questions.', 'success');
        } else {
            throw new Error(result.message || 'Upload failed');
        }
    } catch (error) {
        showAlert(`Upload failed: ${error.message}`, 'danger');
    } finally {
        hideLoading();
    }
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    
    // Initialize page-specific functionality
    const path = window.location.pathname;
    
    if (path === '/' || path === '/index.html') {
        loadDashboard();
    } else if (path === '/analyze') {
        initUploadZone();
    } else if (path === '/compare') {
        initCompareUploadZones();
        loadDocumentsForComparison();
    } else if (path === '/chat') {
        initChatUploadZone();
    }
});
