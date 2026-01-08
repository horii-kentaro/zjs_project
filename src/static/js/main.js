// Global state
let currentPage = 1;
let currentPageSize = 50;
let currentSortBy = 'modified_date';
let currentSortOrder = 'desc';
let currentSearch = '';
let debounceTimer = null;

// Initialize page on load
document.addEventListener('DOMContentLoaded', function() {
    loadVulnerabilities();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Search input with debounce
    document.getElementById('searchInput').addEventListener('input', function(e) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            currentSearch = e.target.value;
            currentPage = 1;
            loadVulnerabilities();
        }, 500);
    });

    // Sort select
    document.getElementById('sortSelect').addEventListener('change', function(e) {
        const parts = e.target.value.split('_');
        const sortOrder = parts.pop(); // 最後の要素がソート順序（asc/desc）
        const sortBy = parts.join('_'); // 残りがソートフィールド
        currentSortBy = sortBy;
        currentSortOrder = sortOrder;
        currentPage = 1;
        loadVulnerabilities();
    });

    // Modal close on background click
    document.getElementById('detailModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
}

// Load vulnerabilities from API
async function loadVulnerabilities() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: currentPageSize,
            sort_by: currentSortBy,
            sort_order: currentSortOrder
        });

        if (currentSearch) {
            params.append('search', currentSearch);
        }

        const response = await fetch(`/api/vulnerabilities?${params.toString()}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        renderVulnerabilities(data.items);
        renderPagination(data);
    } catch (error) {
        console.error('Error loading vulnerabilities:', error);
        showError('脆弱性情報の読み込みに失敗しました。');
    }
}

// Render vulnerabilities table
function renderVulnerabilities(items) {
    const tbody = document.getElementById('vulnerabilityTableBody');

    if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">該当する脆弱性が見つかりませんでした。</td></tr>';
        return;
    }

    tbody.innerHTML = items.map(item => `
        <tr>
            <td class="cve-id">${escapeHtml(item.cve_id)}</td>
            <td>${escapeHtml(item.title)}</td>
            <td><span class="severity severity-${getSeverityClass(item.severity)}">${escapeHtml(item.severity || 'N/A')}</span></td>
            <td>${formatDate(item.published_date)}</td>
            <td>${formatDate(item.modified_date)}</td>
            <td><button class="btn-details" onclick="openModal('${escapeHtml(item.cve_id)}')">詳細表示</button></td>
        </tr>
    `).join('');
}

// Render pagination controls
function renderPagination(data) {
    const pagination = document.getElementById('pagination');
    const { page, total_pages } = data;

    let html = '';

    // Previous button
    html += `<button class="page-btn" ${page === 1 ? 'disabled' : ''} onclick="changePage(${page - 1})">&lt;</button>`;

    // Page numbers
    const maxVisiblePages = 7;
    let startPage = Math.max(1, page - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(total_pages, startPage + maxVisiblePages - 1);

    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    if (startPage > 1) {
        html += `<button class="page-btn" onclick="changePage(1)">1</button>`;
        if (startPage > 2) {
            html += '<span class="page-info">...</span>';
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="page-btn ${i === page ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    }

    if (endPage < total_pages) {
        if (endPage < total_pages - 1) {
            html += '<span class="page-info">...</span>';
        }
        html += `<button class="page-btn" onclick="changePage(${total_pages})">${total_pages}</button>`;
    }

    // Next button
    html += `<button class="page-btn" ${page === total_pages ? 'disabled' : ''} onclick="changePage(${page + 1})">&gt;</button>`;

    pagination.innerHTML = html;
}

// Change page
function changePage(page) {
    currentPage = page;
    loadVulnerabilities();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Open modal with vulnerability details
async function openModal(cveId) {
    try {
        const response = await fetch(`/api/vulnerabilities/${encodeURIComponent(cveId)}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        populateModal(data);
        document.getElementById('detailModal').classList.add('show');
    } catch (error) {
        console.error('Error loading vulnerability details:', error);
        alert('脆弱性の詳細情報の読み込みに失敗しました。');
    }
}

// Close modal
function closeModal() {
    document.getElementById('detailModal').classList.remove('show');
}

// Populate modal with vulnerability data
function populateModal(data) {
    document.getElementById('modalCveId').textContent = data.cve_id;
    document.getElementById('modalTitle').textContent = data.title;

    // Severity
    const severityHtml = `<span class="severity severity-${getSeverityClass(data.severity)}">${escapeHtml(data.severity || 'N/A')}</span>`;
    document.getElementById('modalSeverity').innerHTML = severityHtml;

    // CVSS Score
    document.getElementById('modalCvssScore').textContent = data.cvss_score ? data.cvss_score.toFixed(1) : 'N/A';

    // Dates
    document.getElementById('modalDates').textContent = `${formatDate(data.published_date)} / ${formatDate(data.modified_date)}`;

    // Description
    document.getElementById('modalDescription').textContent = data.description;

    // Affected Products
    if (data.affected_products && data.affected_products.products) {
        const productsList = data.affected_products.products.map(p => `<li>${escapeHtml(p)}</li>`).join('');
        document.getElementById('modalAffectedProducts').innerHTML = `<ul>${productsList}</ul>`;
        document.getElementById('modalAffectedProductsSection').style.display = 'block';
    } else {
        document.getElementById('modalAffectedProductsSection').style.display = 'none';
    }

    // Vendor Info
    if (data.vendor_info && data.vendor_info.vendors) {
        const vendorsList = data.vendor_info.vendors.map(v => `<li>${escapeHtml(v)}</li>`).join('');
        document.getElementById('modalVendorInfo').innerHTML = `<ul>${vendorsList}</ul>`;
        document.getElementById('modalVendorInfoSection').style.display = 'block';
    } else {
        document.getElementById('modalVendorInfoSection').style.display = 'none';
    }

    // References
    if (data.references) {
        let refList = '';
        if (data.references.jvn) {
            refList += `<li><a href="${escapeHtml(data.references.jvn)}" target="_blank">JVN iPedia</a></li>`;
        }
        if (data.references.nvd) {
            refList += `<li><a href="${escapeHtml(data.references.nvd)}" target="_blank">NVD</a></li>`;
        }
        if (data.references.cwe) {
            refList += `<li>${escapeHtml(data.references.cwe)}</li>`;
        }
        document.getElementById('modalReferences').innerHTML = `<ul>${refList}</ul>`;
        document.getElementById('modalReferencesSection').style.display = refList ? 'block' : 'none';
    } else {
        document.getElementById('modalReferencesSection').style.display = 'none';
    }
}

// Utility functions
function getSeverityClass(severity) {
    if (!severity) return '';
    return severity.toLowerCase();
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function showError(message) {
    const tbody = document.getElementById('vulnerabilityTableBody');
    tbody.innerHTML = `<tr><td colspan="6" class="loading" style="color: #d32f2f;">${escapeHtml(message)}</td></tr>`;
}
