# 곡소리 매매법 - NCP(네이버 클라우드) 배포 가이드

## 📋 사전 준비 (필수)

### 1. NCP 서버 정보 수집
아래 정보를 NCP 콘솔에서 확인하고 메모해주세요:

```
[ ] 서버 공인 IP 주소: ________________
[ ] 서버 포트 (기본: 22): ________________
[ ] OS 종류 (Ubuntu/CentOS): ________________
[ ] 서버 root 비밀번호: ________________
    또는
[ ] SSH 개인키 파일 (.pem): ________________

[ ] DB 호스트 주소: ________________
[ ] DB 포트 (기본: 5432): ________________
[ ] DB 이름: ________________
[ ] DB 사용자명: ________________
[ ] DB 비밀번호: ________________
```

### 2. NCP 방화벽 설정 (필수)
NCP 콘솔 → 시큐리티 → ACL에서 다음 포트를 열어주세요:

```
포트 22   (SSH - 배포용)
포트 80   (HTTP)
포트 443  (HTTPS - 향후)
포트 8000 (FastAPI 개발)
```

---

## 🚀 자동 배포 스크립트 (원클릭 배포)

아래 스크립트를 사용하면 모든 설정과 배포를 자동으로 진행합니다.

### Step 1: 배포 설정 파일 생성

`scripts/deploy.sh` 파일을 열고 다음 정보를 입력하세요:

```bash
# NCP 서버 접속 정보
NCP_SERVER_IP="YOUR_NCP_IP"          # 예: 210.89.220.100
NCP_SERVER_USER="root"                # 기본값
NCP_SERVER_PASSWORD="YOUR_PASSWORD"   # 또는 SSH 키 사용

# DB 접속 정보
DB_HOST="YOUR_DB_HOST"                # 예: 210.89.220.101
DB_PORT="5432"
DB_NAME="goksori_db"
DB_USER="postgres"
DB_PASSWORD="YOUR_DB_PASSWORD"
```

### Step 2: 배포 실행

```bash
# 로컬에서 실행 (NCP 서버에 접속해서 배포)
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 또는 직접 NCP 서버에 SSH 접속 후 실행
ssh -i YOUR_KEY.pem root@YOUR_NCP_IP
cd /home/goksori
./deploy.sh
```

---

## 📝 수동 배포 (단계별)

자동 스크립트가 작동하지 않을 경우, 다음 단계를 수동으로 진행하세요.

### Step 1: NCP 서버에 SSH 접속

```bash
# SSH 키 사용 (권장)
ssh -i /path/to/your-key.pem root@YOUR_NCP_IP

# 또는 비밀번호 사용
ssh root@YOUR_NCP_IP
# 비밀번호 입력
```

### Step 2: 시스템 업데이트

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3-pip postgresql-client git nginx
```

### Step 3: 프로젝트 클론

```bash
cd /home
git clone https://github.com/yourname/goksori.git
cd goksori/backend
```

### Step 4: Python 가상환경 설정

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 5: 환경 설정

```bash
cp config/.env.example config/.env
nano config/.env
```

다음 내용 수정:

```ini
# Database
DATABASE_URL=postgresql://postgres:PASSWORD@YOUR_DB_HOST:5432/goksori_db

# App
SECRET_KEY=your-secure-random-key-here-change-this
APP_ENV=production
DEBUG=false

# DART API (선택)
DART_API_KEY=your-dart-key

# AdSense (선택)
ADSENSE_CLIENT_ID=ca-pub-your-id
```

### Step 6: Systemd 서비스 설정

```bash
sudo nano /etc/systemd/system/goksori.service
```

다음 내용 입력:

```ini
[Unit]
Description=Goksori Trading Signal Service
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/home/goksori/backend
Environment="PATH=/home/goksori/backend/venv/bin"
ExecStart=/home/goksori/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable goksori
sudo systemctl start goksori
sudo systemctl status goksori  # 상태 확인
```

### Step 7: Nginx 리버스 프록시 설정

```bash
sudo nano /etc/nginx/sites-available/goksori
```

다음 내용 입력:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.com;  # 또는 서버 IP

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /home/goksori/frontend/static/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/goksori /etc/nginx/sites-enabled/
sudo nginx -t  # 문법 검사
sudo systemctl restart nginx
```

### Step 8: HTTPS 설정 (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d YOUR_DOMAIN.com
```

---

## ✅ 배포 후 확인 (필수!)

### 1. 서비스 상태 확인

```bash
# 서비스가 실행 중인지 확인
sudo systemctl status goksori

# 로그 확인
sudo journalctl -u goksori -f

# Nginx 상태
sudo systemctl status nginx
```

### 2. API 테스트

```bash
# 서버에서 직접 테스트
curl http://127.0.0.1:8000/health

# 외부에서 테스트 (로컬 터미널)
curl http://YOUR_NCP_IP/health
```

### 3. 웹사이트 접속

```
http://YOUR_NCP_IP
또는
http://YOUR_DOMAIN.com (도메인 설정 후)
```

---

## 🐛 트러블슈팅

### 서비스가 시작되지 않음

```bash
# 상세 로그 확인
sudo journalctl -u goksori -n 50

# Python 직접 실행으로 에러 확인
cd /home/goksori/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### DB 연결 실패

```bash
# PostgreSQL 연결 테스트
psql -h YOUR_DB_HOST -U postgres -d goksori_db -c "SELECT 1;"

# .env 파일 DATABASE_URL 다시 확인
cat config/.env | grep DATABASE_URL
```

### Nginx 연결 안 됨

```bash
# Nginx 문법 확인
sudo nginx -t

# 방화벽 확인
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Nginx 프로세스 확인
ps aux | grep nginx
```

### 포트 이미 사용 중

```bash
# 포트 8000 사용 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

---

## 📊 모니터링 & 로그

### 실시간 로그 모니터링

```bash
# 서비스 로그
sudo journalctl -u goksori -f

# Nginx 접근 로그
tail -f /var/log/nginx/access.log

# Nginx 에러 로그
tail -f /var/log/nginx/error.log
```

### 서버 성능 모니터링

```bash
# CPU, 메모리 사용량
top

# 디스크 사용량
df -h

# 메모리 사용량 상세
free -h
```

---

## 🔄 업데이트 & 유지보수

### 코드 업데이트

```bash
cd /home/goksori
git pull origin main

# 새로운 의존성 설치
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 서비스 재시작
sudo systemctl restart goksori
```

### DB 마이그레이션

```bash
cd /home/goksori/backend
source venv/bin/activate
alembic upgrade head
```

---

## 🔒 보안 체크리스트

```
[ ] SSH 비밀번호 로그인 비활성화 (키만 사용)
[ ] 방화벽에서 필요한 포트만 열기
[ ] HTTPS 설정 (Let's Encrypt)
[ ] SECRET_KEY 변경 (프로덕션 보안 키)
[ ] DB 비밀번호 강력하게 설정
[ ] 정기적인 로그 점검
[ ] 백업 설정 (DB, 설정 파일)
```

---

## 📞 문제 해결

### 빠른 문제 진단

```bash
# 현재 배포 상태 확인
./scripts/check-deployment.sh

# 모든 서비스 상태
sudo systemctl status goksori nginx postgresql

# 네트워크 연결 확인
curl -v http://127.0.0.1:8000/health
```

### 응급 재배포

```bash
# 서비스 중지
sudo systemctl stop goksori

# 코드 최신화
cd /home/goksori
git pull origin main

# 의존성 재설치
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 서비스 재시작
sudo systemctl start goksori
sudo systemctl status goksori
```

---

## 💾 백업 & 복구

### DB 백업

```bash
# 풀 백업
pg_dump -h YOUR_DB_HOST -U postgres goksori_db > backup_$(date +%Y%m%d).sql

# 압축 백업
pg_dump -h YOUR_DB_HOST -U postgres goksori_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

### DB 복구

```bash
psql -h YOUR_DB_HOST -U postgres goksori_db < backup_20260219.sql
```

---

**NCP 배포 완료! 🎉**

문제가 발생하면 위 트러블슈팅 섹션을 참고하세요.
