# GitHub Secrets 설정 가이드

CI/CD 파이프라인을 위한 GitHub Secrets를 설정하는 방법입니다.

## 📋 필수 Secrets 목록

### 1. Chargeap 서버 접속 정보

| Secret Name | 설명 | 예시 |
|------------|------|------|
| `CHARGEAP_HOST` | 서버 호스트명 | `d11475.sgp1.stableserver.net` |
| `CHARGEAP_USER` | SSH 사용자명 | `chargeap` |
| `CHARGEAP_SSH_KEY` | SSH Private Key | (아래 생성 방법 참조) |
| `CHARGEAP_DEPLOY_PATH` | 배포 경로 | `/home/chargeap/menu-knowledge` |

### 2. 애플리케이션 환경변수

| Secret Name | 설명 | 예시 |
|------------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `SECRET_KEY` | FastAPI SECRET_KEY | (랜덤 문자열 생성 필요) |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-proj-...` |

---

## 🔑 SSH Key 생성 방법

### 1. 로컬에서 SSH Key 생성

```bash
# 새 SSH 키 생성 (GitHub Actions 전용)
ssh-keygen -t ed25519 -C "github-actions-menu-knowledge" -f ~/.ssh/menu_knowledge_deploy

# Private Key 출력 (GitHub Secret에 등록)
cat ~/.ssh/menu_knowledge_deploy

# Public Key 출력 (서버에 등록)
cat ~/.ssh/menu_knowledge_deploy.pub
```

### 2. 서버에 Public Key 등록

```bash
# 서버에 SSH 접속
ssh chargeap@d11475.sgp1.stableserver.net

# authorized_keys에 Public Key 추가
echo "YOUR_PUBLIC_KEY" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 로그아웃
exit
```

### 3. GitHub에 Private Key 등록

1. GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** 클릭
3. Name: `CHARGEAP_SSH_KEY`
4. Secret: (Private Key 전체 내용 붙여넣기)
5. **Add secret** 클릭

---

## 📝 GitHub Secrets 등록 방법

### Step 1: GitHub 저장소 접속

1. https://github.com/YOUR_USERNAME/menu-knowledge
2. **Settings** 탭 클릭

### Step 2: Secrets 메뉴 이동

1. 왼쪽 메뉴에서 **Secrets and variables** 클릭
2. **Actions** 선택

### Step 3: Secrets 등록

각 Secret을 하나씩 등록:

```
1. New repository secret 클릭
2. Name: CHARGEAP_HOST
3. Secret: d11475.sgp1.stableserver.net
4. Add secret 클릭

(위 과정을 모든 Secrets에 대해 반복)
```

---

## 🔐 SECRET_KEY 생성 방법

```python
# Python으로 랜덤 SECRET_KEY 생성
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

또는

```bash
# OpenSSL로 생성
openssl rand -base64 64
```

---

## ✅ 설정 완료 확인

### 1. Secrets 확인

**Settings → Secrets and variables → Actions**에서 다음 Secrets이 등록되었는지 확인:

- [x] CHARGEAP_HOST
- [x] CHARGEAP_USER
- [x] CHARGEAP_SSH_KEY
- [x] CHARGEAP_DEPLOY_PATH
- [x] DATABASE_URL
- [x] SECRET_KEY
- [x] OPENAI_API_KEY

### 2. SSH 연결 테스트

```bash
# 로컬에서 SSH 연결 테스트
ssh -i ~/.ssh/menu_knowledge_deploy chargeap@d11475.sgp1.stableserver.net
```

성공하면 GitHub Actions도 정상 동작합니다.

---

## 🚀 CI/CD 워크플로우 테스트

### 1. CI 테스트 (Pull Request)

```bash
# 새 브랜치 생성
git checkout -b test/ci-pipeline

# 더미 변경
echo "# CI Test" >> README.md

# 커밋 및 푸시
git add README.md
git commit -m "test: CI pipeline"
git push origin test/ci-pipeline
```

GitHub에서 Pull Request 생성 → **Checks** 탭에서 CI 실행 확인

### 2. CD 테스트 (main 브랜치 머지)

```bash
# main 브랜치로 머지
git checkout main
git merge test/ci-pipeline
git push origin main
```

GitHub Actions → **CD - Deploy to Production** 실행 확인

---

## 🐛 트러블슈팅

### SSH 연결 실패

**에러**: `Permission denied (publickey)`

**해결**:
1. Public Key가 서버의 `~/.ssh/authorized_keys`에 등록되었는지 확인
2. Private Key가 GitHub Secret에 올바르게 등록되었는지 확인
3. SSH Key 권한 확인: `chmod 600 ~/.ssh/authorized_keys`

### 배포 실패

**에러**: `git pull` 실패

**해결**:
1. 서버에 `/home/chargeap/menu-knowledge` 디렉토리 생성
2. Git 저장소 클론: `git clone https://github.com/YOUR_USERNAME/menu-knowledge.git`

---

## 📞 문제 발생 시

- GitHub Actions 로그 확인: **Actions** 탭 → 실패한 워크플로우 클릭
- 서버 로그 확인: `ssh chargeap@... && docker-compose logs backend`
