// Asset Management Page JavaScript

let currentPage = 1;
const pageSize = 50;
let currentSource = '';
let currentAssetId = null;
let currentUploadType = '';

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadAssets();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Source filter
    document.getElementById('sourceFilter').addEventListener('change', (e) => {
        currentSource = e.target.value;
        currentPage = 1;
        loadAssets();
    });

    // File upload drag & drop
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const fileName = e.target.files[0].name;
            dropZone.querySelector('.file-upload-text').textContent = fileName;
        }
    });
}

// Load assets from API
async function loadAssets() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            limit: pageSize
        });

        if (currentSource) {
            params.append('source', currentSource);
        }

        const response = await fetch(`/api/assets?${params}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to load assets');
        }

        renderAssets(data.items);
        renderPagination(data.total, data.page, data.limit);
    } catch (error) {
        console.error('Error loading assets:', error);
        showAlert('資産の読み込みに失敗しました: ' + error.message, 'error');
        document.getElementById('assetsTableBody').innerHTML =
            '<tr><td colspan="8" class="loading">エラーが発生しました</td></tr>';
    }
}

// Render assets table
function renderAssets(assets) {
    const tbody = document.getElementById('assetsTableBody');

    if (assets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">資産が登録されていません</td></tr>';
        return;
    }

    tbody.innerHTML = assets.map(asset => `
        <tr>
            <td>${escapeHtml(asset.asset_name)}</td>
            <td>${escapeHtml(asset.vendor)}</td>
            <td>${escapeHtml(asset.product)}</td>
            <td>${escapeHtml(asset.version)}</td>
            <td style="font-size: 12px; color: #666;">${escapeHtml(asset.cpe_code)}</td>
            <td>
                <span class="severity severity-${getSourceColor(asset.source)}">${getSourceLabel(asset.source)}</span>
            </td>
            <td>${formatDate(asset.created_at)}</td>
            <td>
                <button class="btn-edit" onclick="editAsset('${asset.asset_id}')">編集</button>
                <button class="btn-danger" onclick="deleteAsset('${asset.asset_id}', '${escapeHtml(asset.asset_name)}')">削除</button>
            </td>
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
    loadAssets();
}

// Open create modal
function openCreateModal() {
    currentAssetId = null;
    document.getElementById('modalTitle').textContent = '資産の新規登録';
    document.getElementById('assetForm').reset();
    document.getElementById('assetModal').classList.add('show');
}

// Open upload modal
function openUploadModal(type) {
    currentUploadType = type;
    const titles = {
        composer: 'Composerファイルのアップロード',
        npm: 'NPMファイルのアップロード',
        docker: 'Dockerfileのアップロード'
    };
    const hints = {
        composer: 'composer.json または composer.lock',
        npm: 'package.json または package-lock.json',
        docker: 'Dockerfile'
    };

    document.getElementById('uploadModalTitle').textContent = titles[type];
    document.getElementById('fileHint').textContent = hints[type];
    document.getElementById('uploadForm').reset();
    document.querySelector('.file-upload-text').textContent = 'ファイルをドラッグ&ドロップ';
    document.getElementById('uploadModal').classList.add('show');
}

// Close modals
function closeAssetModal() {
    document.getElementById('assetModal').classList.remove('show');
}

function closeUploadModal() {
    document.getElementById('uploadModal').classList.remove('show');
}

// Save asset
async function saveAsset(event) {
    event.preventDefault();

    const assetData = {
        asset_name: document.getElementById('assetName').value,
        vendor: document.getElementById('vendor').value,
        product: document.getElementById('product').value,
        version: document.getElementById('version').value
    };

    try {
        const url = currentAssetId
            ? `/api/assets/${currentAssetId}`
            : '/api/assets';
        const method = currentAssetId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(assetData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to save asset');
        }

        showAlert(
            currentAssetId ? '資産を更新しました' : '資産を登録しました',
            'success'
        );
        closeAssetModal();
        loadAssets();
    } catch (error) {
        console.error('Error saving asset:', error);
        showAlert('資産の保存に失敗しました: ' + error.message, 'error');
    }
}

// Edit asset
async function editAsset(assetId) {
    try {
        const response = await fetch(`/api/assets/${assetId}`);
        const asset = await response.json();

        if (!response.ok) {
            throw new Error(asset.detail || 'Failed to load asset');
        }

        currentAssetId = assetId;
        document.getElementById('modalTitle').textContent = '資産の編集';
        document.getElementById('assetName').value = asset.asset_name;
        document.getElementById('vendor').value = asset.vendor;
        document.getElementById('product').value = asset.product;
        document.getElementById('version').value = asset.version;
        document.getElementById('assetModal').classList.add('show');
    } catch (error) {
        console.error('Error loading asset:', error);
        showAlert('資産の読み込みに失敗しました: ' + error.message, 'error');
    }
}

// Delete asset
async function deleteAsset(assetId, assetName) {
    if (!confirm(`「${assetName}」を削除しますか？\n関連するマッチング結果も削除されます。`)) {
        return;
    }

    try {
        const response = await fetch(`/api/assets/${assetId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to delete asset');
        }

        showAlert('資産を削除しました', 'success');
        loadAssets();
    } catch (error) {
        console.error('Error deleting asset:', error);
        showAlert('資産の削除に失敗しました: ' + error.message, 'error');
    }
}

// Upload file
async function uploadFile(event) {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files || fileInput.files.length === 0) {
        showAlert('ファイルを選択してください', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'アップロード中...';

    try {
        const response = await fetch(`/api/assets/import/${currentUploadType}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to upload file');
        }

        showAlert(
            `${data.imported_count}件の資産を登録しました ` +
            `(スキップ: ${data.skipped_count}件)`,
            'success'
        );
        closeUploadModal();
        loadAssets();
    } catch (error) {
        console.error('Error uploading file:', error);
        showAlert('ファイルのアップロードに失敗しました: ' + error.message, 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'アップロード';
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
    }, 5000);
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP');
}

function getSourceLabel(source) {
    const labels = {
        manual: '手動',
        composer: 'Composer',
        npm: 'NPM',
        docker: 'Docker'
    };
    return labels[source] || source;
}

function getSourceColor(source) {
    const colors = {
        manual: 'low',
        composer: 'medium',
        npm: 'high',
        docker: 'critical'
    };
    return colors[source] || 'low';
}
