// Matching Results Page JavaScript

let currentPage = 1;
const pageSize = 50;
let currentSeverity = '';
let currentSource = '';

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadMatchingResults();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Severity filter
    document.getElementById('severityFilter').addEventListener('change', (e) => {
        currentSeverity = e.target.value;
        currentPage = 1;
        loadMatchingResults();
    });

    // Source filter
    document.getElementById('sourceFilter').addEventListener('change', (e) => {
        currentSource = e.target.value;
        currentPage = 1;
        loadMatchingResults();
    });
}

// Load dashboard statistics
async function loadDashboard() {
    try {
        const response = await fetch('/api/matching/dashboard');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to load dashboard');
        }

        document.getElementById('affectedAssetsCount').textContent = data.affected_assets_count;
        document.getElementById('criticalCount').textContent = data.critical_vulnerabilities;
        document.getElementById('highCount').textContent = data.high_vulnerabilities;
        document.getElementById('mediumCount').textContent = data.medium_vulnerabilities;
        document.getElementById('lowCount').textContent = data.low_vulnerabilities;
        document.getElementById('totalMatches').textContent = data.total_matches;
        document.getElementById('lastMatchingAt').textContent =
            data.last_matching_at ? formatDateTime(data.last_matching_at) : '未実行';
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showAlert('ダッシュボードの読み込みに失敗しました: ' + error.message, 'error');
    }
}

// Load matching results
async function loadMatchingResults() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            limit: pageSize
        });

        if (currentSeverity) {
            params.append('severity', currentSeverity);
        }

        if (currentSource) {
            params.append('source', currentSource);
        }

        const response = await fetch(`/api/matching/results?${params}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to load matching results');
        }

        renderMatchingResults(data.items);
        renderPagination(data.total, data.page, data.limit);
    } catch (error) {
        console.error('Error loading matching results:', error);
        showAlert('マッチング結果の読み込みに失敗しました: ' + error.message, 'error');
        document.getElementById('matchingTableBody').innerHTML =
            '<tr><td colspan="7" class="loading">エラーが発生しました</td></tr>';
    }
}

// Render matching results table
function renderMatchingResults(results) {
    const tbody = document.getElementById('matchingTableBody');

    if (results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">マッチング結果がありません</td></tr>';
        return;
    }

    tbody.innerHTML = results.map(result => `
        <tr>
            <td>${escapeHtml(result.asset_name)}</td>
            <td>
                <span class="cve-id">${escapeHtml(result.cve_id)}</span>
            </td>
            <td>${escapeHtml(result.vulnerability_title)}</td>
            <td>
                <span class="severity severity-${result.severity ? result.severity.toLowerCase() : 'low'}">
                    ${result.severity || '-'}
                </span>
            </td>
            <td>${result.cvss_score !== null ? result.cvss_score.toFixed(1) : '-'}</td>
            <td>${getMatchReasonLabel(result.match_reason)}</td>
            <td>${formatDateTime(result.matched_at)}</td>
        </tr>
    `).join('');
}

// Render pagination
function renderPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const pagination = document.getElementById('pagination');

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = `
        <button class="page-btn" ${page === 1 ? 'disabled' : ''} onclick="changePage(${page - 1})">← 前へ</button>
    `;

    // Page numbers
    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        html += `
            <button class="page-btn ${i === page ? 'active' : ''}" onclick="changePage(${i})">${i}</button>
        `;
    }

    if (totalPages > 10) {
        html += '<span class="page-info">...</span>';
    }

    html += `
        <button class="page-btn" ${page === totalPages ? 'disabled' : ''} onclick="changePage(${page + 1})">次へ →</button>
        <span class="page-info">${total}件中 ${(page - 1) * limit + 1}-${Math.min(page * limit, total)}件</span>
    `;

    pagination.innerHTML = html;
}

// Change page
function changePage(page) {
    currentPage = page;
    loadMatchingResults();
}

// Execute matching
async function executeMatching() {
    const executeBtn = document.getElementById('executeBtn');
    const executeBtnText = document.getElementById('executeBtnText');
    const executeBtnSpinner = document.getElementById('executeBtnSpinner');

    executeBtn.disabled = true;
    executeBtnText.textContent = 'マッチング実行中...';
    executeBtnSpinner.style.display = 'inline-block';

    try {
        const response = await fetch('/api/matching/execute', {
            method: 'POST'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to execute matching');
        }

        showAlert(
            `マッチング完了: ${data.total_matches}件のマッチング ` +
            `(完全一致: ${data.exact_matches}, バージョン範囲: ${data.version_range_matches}, ` +
            `ワイルドカード: ${data.wildcard_matches}) ` +
            `実行時間: ${data.execution_time_seconds}秒`,
            'success'
        );

        // Reload dashboard and results
        await loadDashboard();
        currentPage = 1;
        await loadMatchingResults();
    } catch (error) {
        console.error('Error executing matching:', error);
        showAlert('マッチングの実行に失敗しました: ' + error.message, 'error');
    } finally {
        executeBtn.disabled = false;
        executeBtnText.textContent = 'マッチング実行';
        executeBtnSpinner.style.display = 'none';
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    alertContainer.innerHTML = '';
    alertContainer.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 10000); // 10 seconds for matching results
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP');
}

function getMatchReasonLabel(reason) {
    const labels = {
        exact_match: '完全一致',
        version_range: 'バージョン範囲',
        wildcard_match: 'ワイルドカード'
    };
    return labels[reason] || reason;
}
