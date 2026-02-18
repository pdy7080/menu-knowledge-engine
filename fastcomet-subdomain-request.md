# FastComet 지원팀: 서브도메인 설정 요청

---

## 📧 이메일 본문 (정중한 요청)

**Subject:** Request for Nginx Configuration & Subdomain Setup (menu-knowledge.chargeapp.net)

---

Hello Raqel and FastComet Support Team,

Thank you for the excellent support so far with our Menu Knowledge Engine deployment.

### 📌 Current Status

We have successfully:
- ✅ Deployed Menu Knowledge Engine (Python FastAPI) on port 8001
- ✅ Initialized PostgreSQL database with 112 menus
- ✅ Passed all production tests and P0 bug verification
- ✅ Created subdomain directory structure

**What we need:**
We would like to configure a subdomain for our production API following the same pattern as our other services (the-room.chargeapp.net, creator-hub.chargeapp.net).

### 🎯 Request Details

**Subdomain:** menu-knowledge.chargeapp.net

**Purpose:** Proxy requests from menu-knowledge.chargeapp.net → localhost:8001 (FastAPI application)

**What we've prepared:**

1. **Directory Structure:** `/home/chargeap/menu-knowledge.chargeapp.net/`
2. **Process Management:** PM2 ecosystem.config.js
3. **Nginx Configuration:** Ready for installation

### 📋 Required Actions (by your team)

We respectfully request your team to:

1. **Create Nginx reverse proxy configuration** with the following settings:

```nginx
upstream menu_knowledge_api {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name menu-knowledge.chargeapp.net;
    client_max_body_size 50M;

    location / {
        proxy_pass http://menu_knowledge_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        access_log off;
        proxy_pass http://menu_knowledge_api;
    }
}
```

**File location:** `/etc/nginx/sites-available/menu-knowledge.chargeapp.net`

2. **Create symbolic link:**
```bash
ln -s /etc/nginx/sites-available/menu-knowledge.chargeapp.net /etc/nginx/sites-enabled/
```

3. **Test and reload Nginx:**
```bash
nginx -t
systemctl restart nginx
```

4. **Enable HTTPS with Let's Encrypt (optional but recommended):**
```bash
certbot certonly --nginx -d menu-knowledge.chargeapp.net
```

### ❓ Questions

1. Is it possible for your team to create this Nginx configuration?
2. If yes, what is the expected timeline?
3. Will Let's Encrypt SSL be automatically set up, or should we request separately?

### 🔒 Security Notes

- No elevated privileges required from our side
- Nginx configuration is standard proxy setup
- Traffic remains internal (127.0.0.1:8001)
- No database or API keys exposed

### 📞 Contact Information

- **Account:** chargeap
- **Server:** d11475.sgp1.stableserver.net
- **Service:** Menu Knowledge Engine v0.1.0
- **Current Status:** Health check passing, Production ready

We truly appreciate your support and look forward to this configuration being set up so we can route traffic through the proper subdomain.

**Kind regards,**

Menu Knowledge Engine Development Team

---

---

## 🎯 한국어 버전 (대안)

### 제목: Nginx 설정 및 서브도메인 구성 요청 (menu-knowledge.chargeapp.net)

FastComet 지원팀 여러분께,

항상 훌륭한 지원을 제공해주셔서 감사합니다. Menu Knowledge Engine 배포가 성공적으로 진행되고 있습니다.

**현재 상태:**
- ✅ Menu Knowledge Engine (Python FastAPI) 포트 8001에 배포 완료
- ✅ PostgreSQL 데이터베이스 초기화 완료 (메뉴 112개)
- ✅ 프로덕션 테스트 및 모든 버그 수정 검증 완료
- ✅ 서브도메인 디렉토리 구조 생성 완료

**요청 사항:**
기존 프로젝트들(the-room.chargeapp.net, creator-hub.chargeapp.net)과 동일한 패턴으로 서브도메인을 구성하고 싶습니다.

**서브도메인:** menu-knowledge.chargeapp.net

**필요한 작업:**

귀사 팀에서 다음을 수행해주시기를 정중히 요청합니다:

1. **Nginx 역프록시 설정** 생성
2. **심볼릭 링크** 생성: `/etc/nginx/sites-available/` → `/etc/nginx/sites-enabled/`
3. **Nginx 테스트 및 재시작**
4. **Let's Encrypt HTTPS 설정** (옵션)

위의 Nginx 설정 내용을 참고해주세요.

**예상되는 timeline:** 언제쯤 가능한지 알려주시면 감사하겠습니다.

감사합니다,

Menu Knowledge Engine 개발팀

---

## 📌 추가 정보

### 우리가 이미 준비한 것:

✅ **서브도메인 디렉토리 구조**
```
/home/chargeap/menu-knowledge.chargeapp.net/
├── app → /home/chargeap/menu-knowledge (심링크)
├── logs → /home/chargeap/menu-knowledge/app/backend/logs (심링크)
└── ecosystem.config.js (PM2 설정)
```

✅ **PM2 설정 파일**
- 프로세스 자동 관리
- 로그 자동 로테이션
- 자동 재시작

✅ **Nginx 역프록시 설정**
- 포트 8001 → menu-knowledge.chargeapp.net 매핑
- WebSocket 지원
- 헤더 전달 설정

### FastComet에서 수행해야 할 것:

❌ Sudo 권한 필요 (우리는 chargeap 사용자)
- Nginx 설정 파일 생성
- 심볼릭 링크 생성
- Nginx 재시작

### 다음 단계:

1. FastComet에 위 요청서 전달
2. 지원팀 승인 대기 (예상 1-2일)
3. Nginx 설정 완료 후 도메인 테스트
4. SSL 인증서 설정 (자동 또는 지원팀)

---

**이 요청서를 FastComet 지원팀에 전달해주세요!** ✉️
