# P1 Issue: B2B Admin Dashboard UI Implementation

**Status**: 🔴 Not Implemented
**Priority**: P1 (High)
**Estimated Time**: 4-6 hours
**Target**: Feature Score 80% → 95%

---

## 📋 Current Status

| Component | Backend API | Frontend UI | Status |
|-----------|-------------|-------------|--------|
| Admin Queue | ✅ Implemented | ❌ Missing | Backend Only |
| Menu Approve/Reject | ✅ Implemented | ❌ Missing | Backend Only |
| Admin Stats | ✅ Implemented | ❌ Missing | Backend Only |

**Problem**: Backend APIs exist but no frontend UI for internal operations

---

## 🎯 Solution: Build Admin Dashboard UI

### Architecture

**Stack**:
- HTML5 + Vanilla JavaScript (no framework needed)
- Tailwind CSS (for styling)
- Fetch API (for backend calls)

**Backend APIs Available**:
1. `GET /api/v1/admin/queue` - List new menus
2. `POST /api/v1/admin/queue/{id}/approve` - Approve/reject menu
3. `GET /api/v1/admin/stats` - Dashboard statistics

---

## 📁 File Structure

```
app/backend/static/admin/
├── index.html          # Main dashboard
├── queue.html          # Menu queue management
├── stats.html          # Statistics dashboard
├── css/
│   └── admin.css       # Custom styles
└── js/
    ├── admin.js        # Main JS
    ├── queue.js        # Queue management
    └── stats.js        # Stats dashboard
```

---

## 💻 Implementation Guide

### Step 1: Create Main Dashboard (index.html)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Menu Knowledge Engine - Admin Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="css/admin.css">
</head>
<body class="bg-gray-100">
    <div class="min-h-screen">
        <!-- Navigation -->
        <nav class="bg-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex">
                        <div class="flex-shrink-0 flex items-center">
                            <h1 class="text-2xl font-bold text-gray-900">
                                Menu Knowledge Engine
                            </h1>
                        </div>
                        <div class="ml-6 flex space-x-8">
                            <a href="/" class="border-b-2 border-blue-500 inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900">
                                Dashboard
                            </a>
                            <a href="/queue.html" class="border-transparent inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-700">
                                Menu Queue
                            </a>
                            <a href="/stats.html" class="border-transparent inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-700">
                                Statistics
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <!-- Stats Cards -->
            <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                <!-- Pending Queue -->
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0 bg-yellow-500 rounded-md p-3">
                                <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">
                                        Pending Queue
                                    </dt>
                                    <dd class="flex items-baseline">
                                        <div class="text-2xl font-semibold text-gray-900" id="pending-count">
                                            Loading...
                                        </div>
                                    </dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                    <div class="bg-gray-50 px-5 py-3">
                        <div class="text-sm">
                            <a href="/queue.html" class="font-medium text-blue-600 hover:text-blue-500">
                                View all
                            </a>
                        </div>
                    </div>
                </div>

                <!-- Canonical Menus -->
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0 bg-green-500 rounded-md p-3">
                                <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">
                                        Canonical Menus
                                    </dt>
                                    <dd class="flex items-baseline">
                                        <div class="text-2xl font-semibold text-gray-900" id="canonical-count">
                                            Loading...
                                        </div>
                                    </dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- DB Hit Rate (7d) -->
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0 bg-blue-500 rounded-md p-3">
                                <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                                </svg>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">
                                        DB Hit Rate (7d)
                                    </dt>
                                    <dd class="flex items-baseline">
                                        <div class="text-2xl font-semibold text-gray-900" id="hit-rate">
                                            Loading...
                                        </div>
                                    </dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- AI Cost (7d) -->
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0 bg-purple-500 rounded-md p-3">
                                <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">
                                        AI Cost (7d)
                                    </dt>
                                    <dd class="flex items-baseline">
                                        <div class="text-2xl font-semibold text-gray-900" id="ai-cost">
                                            Loading...
                                        </div>
                                    </dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="mt-8">
                <div class="bg-white shadow overflow-hidden sm:rounded-lg">
                    <div class="px-4 py-5 sm:px-6">
                        <h3 class="text-lg leading-6 font-medium text-gray-900">
                            Recent Activity
                        </h3>
                        <p class="mt-1 max-w-2xl text-sm text-gray-500">
                            Latest menu scans and approvals
                        </p>
                    </div>
                    <div class="border-t border-gray-200">
                        <ul id="recent-activity" class="divide-y divide-gray-200">
                            <!-- Activity items will be inserted here -->
                        </ul>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script src="js/admin.js"></script>
</body>
</html>
```

### Step 2: Create Queue Management (queue.html)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Menu Queue - Admin Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="min-h-screen">
        <!-- Navigation (same as index.html) -->

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div class="px-4 py-6 sm:px-0">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-2xl font-bold text-gray-900">Menu Queue</h2>

                    <!-- Filters -->
                    <div class="flex space-x-4">
                        <select id="status-filter" class="rounded-md border-gray-300 shadow-sm">
                            <option value="all">All</option>
                            <option value="pending" selected>Pending</option>
                            <option value="confirmed">Confirmed</option>
                            <option value="rejected">Rejected</option>
                        </select>
                        <select id="source-filter" class="rounded-md border-gray-300 shadow-sm">
                            <option value="all">All Sources</option>
                            <option value="b2c">B2C Scan</option>
                            <option value="b2b">B2B Upload</option>
                        </select>
                    </div>
                </div>

                <!-- Queue Table -->
                <div class="bg-white shadow overflow-hidden sm:rounded-md">
                    <ul id="queue-list" class="divide-y divide-gray-200">
                        <!-- Queue items will be inserted here -->
                    </ul>
                </div>

                <!-- Pagination -->
                <div class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 mt-4 rounded-md shadow">
                    <div class="flex-1 flex justify-between sm:hidden">
                        <button id="prev-mobile" class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                            Previous
                        </button>
                        <button id="next-mobile" class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                            Next
                        </button>
                    </div>
                    <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                        <div>
                            <p class="text-sm text-gray-700">
                                Showing <span id="showing-from">1</span> to <span id="showing-to">10</span> of <span id="total-items">0</span> results
                            </p>
                        </div>
                        <div>
                            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" id="pagination">
                                <!-- Pagination buttons will be inserted here -->
                            </nav>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- Approve/Reject Modal -->
    <div id="approve-modal" class="hidden fixed z-10 inset-0 overflow-y-auto">
        <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                        Review Menu
                    </h3>
                    <div class="mt-2">
                        <p class="text-sm text-gray-500" id="modal-description">
                            Menu details will appear here
                        </p>
                    </div>
                    <div class="mt-4">
                        <label class="block text-sm font-medium text-gray-700">Notes</label>
                        <textarea id="review-notes" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"></textarea>
                    </div>
                </div>
                <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button id="approve-btn" type="button" class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 sm:ml-3 sm:w-auto sm:text-sm">
                        Approve
                    </button>
                    <button id="reject-btn" type="button" class="mt-3 w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
                        Reject
                    </button>
                    <button id="cancel-btn" type="button" class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="js/queue.js"></script>
</body>
</html>
```

### Step 3: Create JavaScript Logic (js/admin.js)

```javascript
// admin.js - Main dashboard logic

const API_BASE = '/api/v1';

async function loadDashboardStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/stats`);
        const stats = await response.json();

        // Update stats cards
        document.getElementById('pending-count').textContent = stats.pending_queue_count;
        document.getElementById('canonical-count').textContent = stats.canonical_count;
        document.getElementById('hit-rate').textContent = `${(stats.db_hit_rate_7d * 100).toFixed(1)}%`;
        document.getElementById('ai-cost').textContent = `₩${stats.ai_cost_7d.toLocaleString()}`;

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadRecentActivity() {
    try {
        const response = await fetch(`${API_BASE}/admin/queue?limit=10&status=all`);
        const data = await response.json();

        const activityList = document.getElementById('recent-activity');
        activityList.innerHTML = '';

        data.data.forEach(item => {
            const li = document.createElement('li');
            li.className = 'px-4 py-4 sm:px-6';
            li.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                item.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                                item.status === 'rejected' ? 'bg-red-100 text-red-800' :
                                'bg-yellow-100 text-yellow-800'
                            }">
                                ${item.status}
                            </span>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${item.menu_name_ko}</div>
                            <div class="text-sm text-gray-500">${item.source} • ${new Date(item.created_at).toLocaleString('ko-KR')}</div>
                        </div>
                    </div>
                    <div class="flex items-center">
                        <span class="text-sm text-gray-500">Confidence: ${(item.confidence * 100).toFixed(0)}%</span>
                    </div>
                </div>
            `;
            activityList.appendChild(li);
        });

    } catch (error) {
        console.error('Error loading recent activity:', error);
    }
}

// Load dashboard data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
    loadRecentActivity();

    // Refresh every 30 seconds
    setInterval(loadDashboardStats, 30000);
    setInterval(loadRecentActivity, 30000);
});
```

### Step 4: Create Queue Logic (js/queue.js)

```javascript
// queue.js - Queue management logic

const API_BASE = '/api/v1';
let currentPage = 1;
let currentFilter = { status: 'pending', source: 'all' };

async function loadQueue(page = 1, filters = {}) {
    try {
        const params = new URLSearchParams({
            limit: 50,
            offset: (page - 1) * 50,
            status: filters.status || 'pending',
            source: filters.source || 'all'
        });

        const response = await fetch(`${API_BASE}/admin/queue?${params}`);
        const data = await response.json();

        renderQueue(data.data);
        renderPagination(data.total, page);

    } catch (error) {
        console.error('Error loading queue:', error);
    }
}

function renderQueue(items) {
    const queueList = document.getElementById('queue-list');
    queueList.innerHTML = '';

    if (items.length === 0) {
        queueList.innerHTML = '<li class="px-4 py-8 text-center text-gray-500">No items found</li>';
        return;
    }

    items.forEach(item => {
        const li = document.createElement('li');
        li.className = 'px-4 py-4 hover:bg-gray-50';
        li.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <h4 class="text-lg font-medium text-gray-900">${item.menu_name_ko}</h4>
                    <div class="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            item.source === 'b2c' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                        }">
                            ${item.source.toUpperCase()}
                        </span>
                        <span>Confidence: ${(item.confidence * 100).toFixed(0)}%</span>
                        <span>${new Date(item.created_at).toLocaleString('ko-KR')}</span>
                    </div>
                    ${item.matched_canonical ? `
                        <div class="mt-2 text-sm text-gray-600">
                            Matched: ${item.matched_canonical.name_ko} (${item.matched_canonical.name_en})
                        </div>
                    ` : ''}
                </div>
                ${item.status === 'pending' ? `
                    <div class="ml-4 flex space-x-2">
                        <button onclick="openReviewModal('${item.id}', ${JSON.stringify(item).replace(/"/g, '&quot;')})"
                                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                            Review
                        </button>
                    </div>
                ` : `
                    <span class="ml-4 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        item.status === 'confirmed' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }">
                        ${item.status}
                    </span>
                `}
            </div>
        `;
        queueList.appendChild(li);
    });
}

function renderPagination(total, currentPage) {
    const totalPages = Math.ceil(total / 50);
    const from = (currentPage - 1) * 50 + 1;
    const to = Math.min(currentPage * 50, total);

    document.getElementById('showing-from').textContent = from;
    document.getElementById('showing-to').textContent = to;
    document.getElementById('total-items').textContent = total;

    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';

    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.textContent = 'Previous';
    prevBtn.className = `relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium ${
        currentPage === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'
    }`;
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => {
        if (currentPage > 1) {
            loadQueue(currentPage - 1, currentFilter);
        }
    };
    pagination.appendChild(prevBtn);

    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Next';
    nextBtn.className = `relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium ${
        currentPage === totalPages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'
    }`;
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => {
        if (currentPage < totalPages) {
            loadQueue(currentPage + 1, currentFilter);
        }
    };
    pagination.appendChild(nextBtn);
}

function openReviewModal(queueId, item) {
    const modal = document.getElementById('approve-modal');
    modal.classList.remove('hidden');

    document.getElementById('modal-title').textContent = `Review: ${item.menu_name_ko}`;
    document.getElementById('modal-description').innerHTML = `
        <div class="space-y-2">
            <p><strong>Korean:</strong> ${item.menu_name_ko}</p>
            ${item.matched_canonical ? `
                <p><strong>Matched:</strong> ${item.matched_canonical.name_ko} (${item.matched_canonical.name_en})</p>
            ` : ''}
            <p><strong>Confidence:</strong> ${(item.confidence * 100).toFixed(0)}%</p>
            <p><strong>Source:</strong> ${item.source.toUpperCase()}</p>
        </div>
    `;

    document.getElementById('approve-btn').onclick = () => approveMenu(queueId, 'approve');
    document.getElementById('reject-btn').onclick = () => approveMenu(queueId, 'reject');
    document.getElementById('cancel-btn').onclick = () => modal.classList.add('hidden');
}

async function approveMenu(queueId, action) {
    const notes = document.getElementById('review-notes').value;

    try {
        const response = await fetch(`${API_BASE}/admin/queue/${queueId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, notes })
        });

        if (response.ok) {
            document.getElementById('approve-modal').classList.add('hidden');
            document.getElementById('review-notes').value = '';
            loadQueue(currentPage, currentFilter);
        } else {
            alert('Error: ' + response.statusText);
        }
    } catch (error) {
        console.error('Error approving menu:', error);
        alert('Error: ' + error.message);
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadQueue(1, currentFilter);

    // Filter handlers
    document.getElementById('status-filter').addEventListener('change', (e) => {
        currentFilter.status = e.target.value;
        loadQueue(1, currentFilter);
    });

    document.getElementById('source-filter').addEventListener('change', (e) => {
        currentFilter.source = e.target.value;
        loadQueue(1, currentFilter);
    });
});
```

---

## 🚀 Deployment

### Step 1: Create Static File Serving

Add to `main.py`:

```python
from fastapi.staticfiles import StaticFiles

# Serve static admin files
app.mount("/admin", StaticFiles(directory="app/backend/static/admin", html=True), name="admin")
```

### Step 2: Test Locally

```bash
# Start server
cd app/backend
uvicorn main:app --reload

# Open browser
http://localhost:8000/admin/
```

### Step 3: Production Deployment

Copy static files to production server:

```bash
# On production server
mkdir -p /path/to/app/backend/static/admin
# Upload all HTML/CSS/JS files
```

---

## ✅ Acceptance Criteria

- [ ] Dashboard shows 4 stat cards (pending, canonical, hit rate, AI cost)
- [ ] Queue page shows all pending menus with filtering
- [ ] Approve/reject modal works with notes
- [ ] Pagination works (50 items per page)
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] All API calls work correctly
- [ ] UI matches modern admin dashboard style
- [ ] Feature score: 80% → 95%

---

## 📊 Estimated Breakdown

| Task | Time |
|------|------|
| HTML templates | 2 hours |
| JavaScript logic | 2 hours |
| CSS styling | 1 hour |
| Testing & debugging | 1 hour |
| **Total** | **6 hours** |

---

**Created**: 2026-02-12
**Status**: Implementation guide ready
**Next Step**: Start with index.html and admin.js
