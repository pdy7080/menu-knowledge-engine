# 🏢 P1 Task: B2B Admin Dashboard UI 개발

**담당팀**: Frontend Team (B2B)
**우선순위**: P1 (1주 이내)
**시간 예상**: 4-6시간
**기술 스택**: HTML5 + CSS3 + Vanilla JS + Bootstrap 5

---

## 📊 현황

**검증 결과**: Feature-Validator 80/100점, Frontend-Tester 95/100점
- ✅ Admin API 백엔드: 100% 완성 (`/api/v1/admin/queue`, `/api/v1/admin/stats`)
- ❌ Admin UI 프론트엔드: 0% (누락)

**영향**:
- 식당 사장님이 신규 메뉴를 직접 검수할 수 없음 → 관리자만 가능
- Admin Dashboard 접근 시 404 에러

---

## 🎯 목표

✅ Admin Dashboard 페이지 완성 (`/admin.html`)
✅ 신규 메뉴 큐(Queue) 관리 UI
✅ 실시간 통계 패널
✅ 메뉴 승인/수정/신규등록 액션

---

## 🛠️ 구현 사항

### 📂 필요한 파일 구조

```
app/frontend-b2b/
├── admin.html                    # 메인 관리자 페이지
├── css/
│   ├── admin-dashboard.css       # 스타일 (Bootstrap 확장)
│   └── admin-responsive.css      # 반응형
└── js/
    ├── admin-api.js              # API 호출 함수
    └── admin-dashboard.js        # 상태 관리 및 UI 로직
```

### 1️⃣ admin.html - 페이지 구조

**목표 레이아웃**: 2열 (main + sidebar)

```html
<!-- 헤더 -->
<header class="navbar navbar-dark bg-primary">
  <div class="container-fluid">
    <span class="navbar-brand mb-0 h1">🍲 Menu Admin - Management Console</span>
    <div class="nav-item dropdown">
      <button class="btn btn-outline-light dropdown-toggle">Admin</button>
    </div>
  </div>
</header>

<!-- 메인 컨텐츠 -->
<div class="container-fluid p-4">
  <div class="row">
    <!-- 왼쪽: 신규 메뉴 큐 (메인, 넓음) -->
    <div class="col-md-9">
      <!-- 필터 탭 -->
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item">
          <a class="nav-link active" href="#" data-filter="all">
            📋 모든 항목 (N)
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#" data-filter="pending">
            ⏳ 검토 필요 (N)
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#" data-filter="auto">
            ✅ 자동 승인 (N)
          </a>
        </li>
      </ul>

      <!-- 큐 리스트 -->
      <div id="queue-list" class="queue-container">
        <!-- 동적 로드: JS에서 생성 -->
      </div>

      <!-- 페이지네이션 -->
      <nav class="mt-3">
        <ul class="pagination">
          <!-- 동적 로드 -->
        </ul>
      </nav>
    </div>

    <!-- 오른쪽: 통계 패널 (sidebar, 300px) -->
    <div class="col-md-3">
      <div class="card border-0 shadow-sm">
        <div class="card-body">
          <h5 class="card-title">📊 실시간 통계</h5>

          <div class="stat-item mb-3">
            <label class="text-muted">Canonical 메뉴</label>
            <div class="stat-value">
              <span id="stat-canonical" class="h3">112</span>
              <small class="text-success">+2 (7일)</small>
            </div>
          </div>

          <div class="stat-item mb-3">
            <label class="text-muted">Modifier 단어</label>
            <div class="stat-value">
              <span id="stat-modifier" class="h3">54</span>
            </div>
          </div>

          <div class="stat-item mb-3">
            <label class="text-muted">DB 히트율 (7일)</label>
            <div class="progress">
              <div id="stat-hit-rate" class="progress-bar" style="width: 72%">
                72%
              </div>
            </div>
          </div>

          <div class="stat-item mb-3">
            <label class="text-muted">AI 비용 (7일)</label>
            <div class="stat-value text-danger">
              <span id="stat-cost">₩12,340</span>
            </div>
          </div>

          <div class="stat-item">
            <label class="text-muted">미검토 큐</label>
            <div class="stat-value">
              <span id="stat-pending" class="h3 text-warning">5</span>
            </div>
          </div>

          <!-- 새로고침 버튼 -->
          <button class="btn btn-sm btn-outline-primary w-100 mt-4" id="refresh-stats">
            🔄 새로고침
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 2️⃣ 큐 아이템 카드 컴포넌트

```html
<!-- 각 큐 항목 -->
<div class="queue-item card mb-3 border-left-success">
  <div class="card-body">
    <div class="row">
      <!-- 왼쪽: 메뉴 정보 -->
      <div class="col-md-8">
        <h6 class="card-title">
          <span class="badge badge-success">✅ HIGH</span>
          <strong>할머니 김치찌개</strong>
        </h6>

        <p class="text-muted mb-2">
          <small>📍 Source: OCR 스캔 | 신뢰도: 92%</small>
        </p>

        <div class="row g-2 mb-2">
          <div class="col-6">
            <small><strong>인식된 이름:</strong> 할머니김치찌개</small>
          </div>
          <div class="col-6">
            <small><strong>매칭:</strong> canonical_menus[42]</small>
          </div>
        </div>

        <div class="row g-2">
          <div class="col-6">
            <small><strong>분해:</strong> 할머니 (modifier) + 김치찌개</small>
          </div>
          <div class="col-6">
            <small><strong>번역:</strong> ✅ EN ✅ JA ✅ ZH</small>
          </div>
        </div>
      </div>

      <!-- 오른쪽: 액션 버튼 -->
      <div class="col-md-4 text-end">
        <div class="btn-group-vertical w-100">
          <button class="btn btn-sm btn-success" data-action="approve" data-id="scan-123">
            ✅ 승인
          </button>
          <button class="btn btn-sm btn-warning" data-action="edit" data-id="scan-123">
            ✏️ 수정
          </button>
          <button class="btn btn-sm btn-info" data-action="new" data-id="scan-123">
            ➕ 신규등록
          </button>
          <button class="btn btn-sm btn-danger" data-action="reject" data-id="scan-123">
            ❌ 거부
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 3️⃣ admin-dashboard.js - 상태 관리 및 API 호출

```javascript
// Admin Dashboard 상태 관리
class AdminDashboard {
  constructor() {
    this.API_URL = 'http://localhost:8000/api/v1';
    this.queue = [];
    this.stats = {};
    this.currentFilter = 'all';
    this.init();
  }

  async init() {
    this.setupEventListeners();
    await this.loadQueue();
    await this.loadStats();
    this.startAutoRefresh(); // 5초마다 통계 갱신
  }

  // 큐 로드
  async loadQueue(limit = 20, offset = 0) {
    try {
      const response = await fetch(
        `${this.API_URL}/admin/queue?status=${this.currentFilter}&limit=${limit}&offset=${offset}`
      );
      const data = await response.json();
      this.queue = data.items;
      this.renderQueue();
    } catch (error) {
      console.error('Failed to load queue:', error);
      this.showNotification('큐 로드 실패', 'error');
    }
  }

  // 통계 로드
  async loadStats() {
    try {
      const response = await fetch(`${this.API_URL}/admin/stats`);
      this.stats = await response.json();
      this.renderStats();
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }

  // 통계 렌더링
  renderStats() {
    document.getElementById('stat-canonical').textContent = this.stats.canonical_count;
    document.getElementById('stat-modifier').textContent = this.stats.modifier_count;
    document.getElementById('stat-hit-rate').style.width =
      (this.stats.db_hit_rate_7d * 100) + '%';
    document.getElementById('stat-hit-rate').textContent =
      (this.stats.db_hit_rate_7d * 100).toFixed(0) + '%';
    document.getElementById('stat-cost').textContent =
      '₩' + this.stats.ai_cost_7d.toLocaleString();
    document.getElementById('stat-pending').textContent =
      this.stats.pending_queue_count;
  }

  // 큐 렌더링
  renderQueue() {
    const container = document.getElementById('queue-list');
    container.innerHTML = this.queue.map(item => this.createQueueItemHTML(item)).join('');
    this.attachQueueEventListeners();
  }

  // 큐 아이템 HTML 생성
  createQueueItemHTML(item) {
    const confidenceBadge = item.confidence > 0.8 ? 'success' :
                           item.confidence > 0.6 ? 'warning' : 'danger';

    return `
      <div class="queue-item card mb-3 border-left-${confidenceBadge}">
        <div class="card-body">
          <div class="row">
            <div class="col-md-8">
              <h6 class="card-title">
                <span class="badge badge-${confidenceBadge}">
                  ${item.confidence > 0.8 ? '✅' : '⚠️'} ${item.confidence.toFixed(0)}%
                </span>
                <strong>${item.menu_name_ko}</strong>
              </h6>
              <p class="text-muted mb-2">
                <small>📍 Source: ${item.source} | 상태: ${item.status}</small>
              </p>
            </div>
            <div class="col-md-4 text-end">
              <button class="btn btn-sm btn-success" data-action="approve" data-id="${item.id}">
                ✅ 승인
              </button>
              <button class="btn btn-sm btn-warning" data-action="edit" data-id="${item.id}">
                ✏️ 수정
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // 이벤트 리스너 설정
  setupEventListeners() {
    document.querySelectorAll('[data-filter]').forEach(tab => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        this.currentFilter = e.target.dataset.filter;
        this.loadQueue();
      });
    });

    document.getElementById('refresh-stats').addEventListener('click', () => {
      this.loadStats();
    });
  }

  // 큐 아이템 이벤트 리스너
  attachQueueEventListeners() {
    document.querySelectorAll('[data-action]').forEach(button => {
      button.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        const id = e.target.dataset.id;
        this.handleAction(action, id);
      });
    });
  }

  // 액션 처리
  async handleAction(action, id) {
    try {
      const response = await fetch(
        `${this.API_URL}/admin/queue/${id}/approve`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action })
        }
      );

      if (response.ok) {
        this.showNotification('작업 완료', 'success');
        this.loadQueue();
        this.loadStats();
      } else {
        throw new Error('API error');
      }
    } catch (error) {
      this.showNotification('작업 실패', 'error');
      console.error(error);
    }
  }

  // 자동 새로고침 (5초마다)
  startAutoRefresh() {
    setInterval(() => this.loadStats(), 5000);
  }

  // 알림 표시
  showNotification(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.insertBefore(alertDiv, document.body.firstChild);
  }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
  window.adminDashboard = new AdminDashboard();
});
```

### 4️⃣ admin-dashboard.css - 스타일링

```css
/* Admin Dashboard 스타일 */
.border-left-success {
  border-left: 4px solid #28a745 !important;
}

.border-left-warning {
  border-left: 4px solid #ffc107 !important;
}

.border-left-danger {
  border-left: 4px solid #dc3545 !important;
}

.queue-item {
  transition: all 0.3s ease;
}

.queue-item:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stat-item {
  padding: 12px 0;
  border-bottom: 1px solid #e9ecef;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-value {
  display: block;
  margin-top: 8px;
  font-weight: bold;
}

/* 반응형 */
@media (max-width: 768px) {
  .col-md-9,
  .col-md-3 {
    margin-bottom: 20px;
  }

  .btn-group-vertical .btn {
    border-radius: 4px;
    margin-bottom: 4px;
  }
}
```

---

## ✅ 체크리스트

### 개발
- [ ] HTML 구조 완성 (헤더, 메인, 사이드바)
- [ ] Bootstrap 5 적용
- [ ] CSS 반응형 (768px 기준)
- [ ] JS API 호출 함수 완성
- [ ] 상태 관리 로직 완성
- [ ] 실시간 통계 자동 갱신 (5초)

### 기능 검증
- [ ] 큐 리스트 로드 및 표시
- [ ] 필터 (전체/검토필요/자동승인) 동작
- [ ] [승인] 버튼 → 메뉴 등록
- [ ] [수정] 버튼 → 모달 열림
- [ ] [신규] 버튼 → 신규 메뉴 등록
- [ ] [거부] 버튼 → 삭제 또는 상태 변경
- [ ] 통계 5초마다 갱신
- [ ] 페이지네이션 동작

### 성능 & 접근성
- [ ] 페이지 로드 < 2초
- [ ] 콘솔 에러 없음
- [ ] 모바일 반응형 (480px 테스트)
- [ ] WCAG 기본 접근성 (alt, label)

### 배포 준비
- [ ] 개발팀 테스트 완료
- [ ] 버그 수정
- [ ] Git commit
  ```bash
  git add app/frontend-b2b/
  git commit -m "Implement Admin Dashboard UI for queue management and real-time stats"
  ```

---

## 🎯 성공 기준

| 항목 | 목표 | 달성 여부 |
|------|------|---------|
| Admin Dashboard 완성 | 100% 구현 | ✅ |
| API 연동 | 모든 엔드포인트 동작 | ✅ |
| 실시간 통계 | 5초 자동 갱신 | ✅ |
| 반응형 | 768px 최적화 | ✅ |
| Feature 점수 | 80 → 95+점 | ✅ |
| 배포 준비도 | CONDITIONAL GO → GO | ✅ |

---

## 💡 추가 개선 (v0.2+)

- [ ] 차트 시각화 (Chart.js: 7일 추세)
- [ ] 메뉴 검색/정렬 기능
- [ ] 배치 작업 (선택된 여러 메뉴 동시 처리)
- [ ] 권한 관리 (Admin/Reviewer 역할)
- [ ] 활동 로그 (Audit trail)
