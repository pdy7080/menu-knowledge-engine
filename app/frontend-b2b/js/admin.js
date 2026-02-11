/**
 * Menu Knowledge Engine - Admin Dashboard
 * Sprint 3 P1-1: Queue Management + Engine Monitoring
 */

// ===========================
// Configuration
// ===========================
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    API_ENDPOINTS: {
        QUEUE: '/api/v1/admin/queue',
        STATS: '/api/v1/admin/stats',
    },
    REFRESH_INTERVAL: 5000, // 5 seconds
};

// ===========================
// State Management
// ===========================
const state = {
    currentTab: 'queue',
    currentFilter: 'all',
    currentSource: 'all',
    queueData: [],
    stats: null,
};

// ===========================
// DOM Elements
// ===========================
const DOM = {
    // Tabs
    navTabs: document.querySelectorAll('.nav-tab'),
    queueTab: document.getElementById('queueTab'),
    statsTab: document.getElementById('statsTab'),

    // Queue
    queueCount: document.getElementById('queueCount'),
    queueList: document.getElementById('queueList'),
    filterBtns: document.querySelectorAll('.filter-btn'),
    sourceBtns: document.querySelectorAll('.source-filter'),
    refreshBtn: document.getElementById('refreshBtn'),

    // Stats
    statsGrid: document.getElementById('statsGrid'),

    // Sidebar
    sidebarCanonical: document.getElementById('sidebarCanonical'),
    sidebarModifiers: document.getElementById('sidebarModifiers'),
    sidebarHitRate: document.getElementById('sidebarHitRate'),
    sidebarAICost: document.getElementById('sidebarAICost'),
    sidebarPending: document.getElementById('sidebarPending'),
    activityFeed: document.getElementById('activityFeed'),

    // Loading
    loadingOverlay: document.getElementById('loadingOverlay'),
};

// ===========================
// UI Functions
// ===========================
function showLoading() {
    DOM.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    DOM.loadingOverlay.classList.add('hidden');
}

function switchTab(tabName) {
    // Update tabs
    DOM.navTabs.forEach(tab => {
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update content
    if (tabName === 'queue') {
        DOM.queueTab.classList.add('active');
        DOM.statsTab.classList.remove('active');
    } else if (tabName === 'stats') {
        DOM.queueTab.classList.remove('active');
        DOM.statsTab.classList.add('active');
    }

    state.currentTab = tabName;
}

// ===========================
// Queue Functions
// ===========================
async function loadQueue() {
    try {
        const url = `${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.QUEUE}?status=${state.currentFilter}&source=${state.currentSource}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        state.queueData = data.data;

        renderQueue();
        updateQueueCount(data.total);

    } catch (error) {
        console.error('Error loading queue:', error);
        DOM.queueList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">❌</div>
                <p>큐 로드 실패: ${error.message}</p>
            </div>
        `;
    }
}

function renderQueue() {
    if (state.queueData.length === 0) {
        DOM.queueList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <p>신규 메뉴가 없습니다</p>
            </div>
        `;
        return;
    }

    const html = state.queueData.map(item => createQueueItem(item)).join('');
    DOM.queueList.innerHTML = html;

    // Add event listeners
    attachQueueActions();
}

function createQueueItem(item) {
    const sourceClass = item.source === 'b2c' ? 'b2c' : 'b2b';
    const sourceLabel = item.source === 'b2c' ? 'B2C 스캔' : 'B2B 업로드';
    const confidencePct = Math.round((item.confidence || 0) * 100);

    let confidenceBadge = '';
    if (confidencePct >= 85) {
        confidenceBadge = '<span class="confidence-badge high">✅ 높은 확신</span>';
    } else if (confidencePct >= 65) {
        confidenceBadge = '<span class="confidence-badge mid">⚠️ 확인 필요</span>';
    } else {
        confidenceBadge = '<span class="confidence-badge low">❓ 낮은 확신</span>';
    }

    return `
        <div class="queue-item" data-id="${item.id}">
            <div class="queue-item-header">
                <div class="queue-menu-name korean-text">${escapeHtml(item.menu_name_ko)}</div>
                <span class="queue-source ${sourceClass}">${sourceLabel}</span>
            </div>

            <div class="queue-item-details">
                <div class="queue-detail-row">
                    <span class="queue-detail-label">등록일:</span>
                    <span>${formatDate(item.created_at)}</span>
                </div>
                <div class="queue-detail-row">
                    <span class="queue-detail-label">신뢰도:</span>
                    <span>${confidencePct}% ${confidenceBadge}</span>
                </div>
                ${item.matched_canonical ? `
                <div class="queue-detail-row">
                    <span class="queue-detail-label">매칭:</span>
                    <span>${escapeHtml(item.matched_canonical.name_ko)} (${escapeHtml(item.matched_canonical.name_en)})</span>
                </div>
                ` : ''}
                <div class="queue-detail-row">
                    <span class="queue-detail-label">상태:</span>
                    <span>${getStatusLabel(item.status)}</span>
                </div>
            </div>

            ${item.status === 'pending' || !item.status ? `
            <div class="queue-item-actions">
                <button class="btn btn-approve" data-action="approve" data-id="${item.id}">
                    ✅ 승인
                </button>
                <button class="btn btn-edit" data-action="edit" data-id="${item.id}">
                    ✏️ 수정
                </button>
                <button class="btn btn-reject" data-action="reject" data-id="${item.id}">
                    ❌ 거부
                </button>
            </div>
            ` : ''}
        </div>
    `;
}

function attachQueueActions() {
    document.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const action = e.target.dataset.action;
            const id = e.target.dataset.id;

            if (confirm(`정말 이 메뉴를 ${action === 'approve' ? '승인' : action === 'reject' ? '거부' : '수정'}하시겠습니까?`)) {
                await performQueueAction(id, action);
            }
        });
    });
}

async function performQueueAction(queueId, action) {
    try {
        showLoading();

        const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.QUEUE}/${queueId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        hideLoading();

        // Reload queue and stats
        await loadQueue();
        await updateStats();

        // Add activity
        addActivity(`메뉴 ${action === 'approve' ? '승인' : action === 'reject' ? '거부' : '수정'}됨`);

    } catch (error) {
        hideLoading();
        alert(`작업 실패: ${error.message}`);
        console.error('Queue action error:', error);
    }
}

function updateQueueCount(count) {
    DOM.queueCount.textContent = `${count}건`;
}

function getStatusLabel(status) {
    switch (status) {
        case 'pending':
            return '⏳ 검토 대기';
        case 'confirmed':
            return '✅ 승인됨';
        case 'rejected':
            return '❌ 거부됨';
        default:
            return '⏳ 대기중';
    }
}

// ===========================
// Stats Functions
// ===========================
async function updateStats() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.STATS}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const stats = await response.json();
        state.stats = stats;

        renderStats();
        updateSidebar();

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function renderStats() {
    if (!state.stats) return;

    const stats = state.stats;

    DOM.statsGrid.innerHTML = `
        <div class="stat-card">
            <div class="stat-card-title">Canonical 메뉴</div>
            <div class="stat-card-value">${stats.canonical_count}</div>
        </div>
        <div class="stat-card">
            <div class="stat-card-title">수식어 사전</div>
            <div class="stat-card-value">${stats.modifier_count}</div>
        </div>
        <div class="stat-card">
            <div class="stat-card-title">DB 히트율 (7일)</div>
            <div class="stat-card-value">${Math.round(stats.db_hit_rate_7d * 100)}%</div>
        </div>
        <div class="stat-card">
            <div class="stat-card-title">평균 신뢰도 (7일)</div>
            <div class="stat-card-value">${Math.round(stats.avg_confidence_7d * 100)}%</div>
        </div>
        <div class="stat-card">
            <div class="stat-card-title">스캔 수 (7일)</div>
            <div class="stat-card-value">${stats.scans_7d}</div>
        </div>
        <div class="stat-card">
            <div class="stat-card-title">AI 비용 (7일)</div>
            <div class="stat-card-value">₩${stats.ai_cost_7d.toLocaleString()}</div>
        </div>
    `;
}

function updateSidebar() {
    if (!state.stats) return;

    const stats = state.stats;

    DOM.sidebarCanonical.textContent = stats.canonical_count;
    DOM.sidebarModifiers.textContent = stats.modifier_count;
    DOM.sidebarHitRate.textContent = `${Math.round(stats.db_hit_rate_7d * 100)}%`;
    DOM.sidebarAICost.textContent = `₩${stats.ai_cost_7d.toLocaleString()}`;
    DOM.sidebarPending.textContent = stats.pending_queue_count;
}

// ===========================
// Activity Feed
// ===========================
function addActivity(text) {
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    activityItem.innerHTML = `
        <span class="activity-time">방금 전</span>
        <span class="activity-text">${escapeHtml(text)}</span>
    `;

    DOM.activityFeed.prepend(activityItem);

    // Keep only last 10 items
    const items = DOM.activityFeed.querySelectorAll('.activity-item');
    if (items.length > 10) {
        items[items.length - 1].remove();
    }
}

// ===========================
// Utility Functions
// ===========================
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return '방금 전';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`;

    return date.toLocaleDateString('ko-KR');
}

// ===========================
// Event Listeners
// ===========================
function initEventListeners() {
    // Tab navigation
    DOM.navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            switchTab(tab.dataset.tab);

            if (tab.dataset.tab === 'stats') {
                updateStats();
            }
        });
    });

    // Filter buttons
    DOM.filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            DOM.filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentFilter = btn.dataset.filter;
            loadQueue();
        });
    });

    // Source buttons
    DOM.sourceBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            DOM.sourceBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentSource = btn.dataset.source;
            loadQueue();
        });
    });

    // Refresh button
    DOM.refreshBtn.addEventListener('click', () => {
        loadQueue();
        updateStats();
        addActivity('수동 새로고침');
    });
}

// ===========================
// Auto Refresh
// ===========================
function startAutoRefresh() {
    setInterval(() => {
        if (state.currentTab === 'queue') {
            loadQueue();
        } else if (state.currentTab === 'stats') {
            updateStats();
        }

        // Always update sidebar
        updateStats();
    }, CONFIG.REFRESH_INTERVAL);
}

// ===========================
// Initialization
// ===========================
async function init() {
    console.log('🔧 Admin Dashboard - Initializing...');

    initEventListeners();

    // Load initial data
    await loadQueue();
    await updateStats();

    // Start auto refresh
    startAutoRefresh();

    addActivity('Admin 대시보드 시작됨');

    console.log('✅ Admin initialized successfully');
}

// Start app
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
