#!/bin/bash
################################################################################
#          곡소리 매매법 - NCP 수동 배포 가이드 (NCP 서버에서 실행)
#
# 사용법:
#  1. NCP 서버에 SSH로 접속
#  2. 아래 스크립트를 서버에 복사해서 실행
#  3. 또는 아래 명령어들을 차례대로 복사해서 실행
################################################################################

set -e

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║   🚀 곡소리 매매법 - NCP 서버 배포 스크립트                   ║
╚════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# ─── 1단계: 시스템 업데이트 ──────────────────────────────────────────────────

echo -e "${BLUE}[1/8] 시스템 패키지 업데이트 중...${NC}"
apt-get update
apt-get install -y python3.10 python3-pip git nginx curl

# ─── 2단계: 프로젝트 클론 또는 다운로드 ──────────────────────────────────────

echo -e "${BLUE}[2/8] 프로젝트 준비 중...${NC}"

# 깃에서 클론하는 경우 (GitHub URL로 변경 필요)
# git clone https://github.com/yourname/goksori.git /home/goksori

# 또는 로컬에서 업로드한 경우
if [ ! -d "/home/goksori" ]; then
    mkdir -p /home/goksori
fi

# 임시 위치에서 복사 (만약 파일이 업로드되었다면)
if [ -f "/tmp/goksori.tar.gz" ]; then
    echo "  /tmp에서 파일 추출 중..."
    cd /tmp
    tar -xzf goksori.tar.gz
    cp -r backend frontend docs scripts config /home/goksori/
fi

cd /home/goksori
echo -e "${GREEN}✅ 프로젝트 준비 완료${NC}"

# ─── 3단계: Python 가상환경 설정 ───────────────────────────────────────────

echo -e "${BLUE}[3/8] Python 가상환경 설정 중...${NC}"
cd /home/goksori/backend
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo -e "${GREEN}✅ Python 환경 설정 완료${NC}"

# ─── 4단계: 환경 설정 파일 작성 ──────────────────────────────────────────

echo -e "${BLUE}[4/8] 환경 설정 파일 작성 중...${NC}"
cat > config/.env << 'ENV_EOF'
# 곡소리 매매법 - NCP 배포 설정
DATABASE_URL=postgresql://days:Project0423!@projectabout-001-8tq0.vpc.nclouddb.com:5432/goksori_db

# 앱 설정
APP_NAME=곡소리매매법
APP_ENV=production
DEBUG=false
SECRET_KEY=goksori-secret-key-change-this-in-production-$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# 크롤링 설정
CRAWL_INTERVAL_HOURS=4
MAX_COMMENTS_PER_STOCK=100
REQUEST_DELAY_SECONDS=1

# DART API (선택)
DART_API_KEY=

# AdSense (선택)
ADSENSE_CLIENT_ID=

# Kakao (선택)
KAKAO_JS_KEY=
ENV_EOF

echo -e "${GREEN}✅ 환경 설정 완료${NC}"

# ─── 5단계: Systemd 서비스 등록 ──────────────────────────────────────────

echo -e "${BLUE}[5/8] Systemd 서비스 등록 중...${NC}"
cat > /etc/systemd/system/goksori.service << 'SYSTEMD_EOF'
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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

systemctl daemon-reload
systemctl enable goksori
echo -e "${GREEN}✅ Systemd 서비스 등록 완료${NC}"

# ─── 6단계: Nginx 설정 ──────────────────────────────────────────────────

echo -e "${BLUE}[6/8] Nginx 리버스 프록시 설정 중...${NC}"
cat > /etc/nginx/sites-available/goksori << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    client_max_body_size 10M;

    # 상태 확인
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
    }

    # API와 정적 파일
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }
}
NGINX_EOF

# Nginx 기본 사이트 비활성화
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/goksori /etc/nginx/sites-enabled/goksori

# 문법 검사
if nginx -t 2>/dev/null; then
    systemctl restart nginx
    echo -e "${GREEN}✅ Nginx 설정 완료${NC}"
else
    echo -e "${RED}❌ Nginx 설정 오류${NC}"
    exit 1
fi

# ─── 7단계: 서비스 시작 ──────────────────────────────────────────────────

echo -e "${BLUE}[7/8] 곡소리 서비스 시작 중...${NC}"
systemctl start goksori
sleep 3

# 상태 확인
if systemctl is-active --quiet goksori; then
    echo -e "${GREEN}✅ 서비스 시작 성공${NC}"
else
    echo -e "${RED}❌ 서비스 시작 실패${NC}"
    echo "로그 확인:"
    journalctl -u goksori -n 20
    exit 1
fi

# ─── 8단계: 최종 확인 ──────────────────────────────────────────────────

echo -e "${BLUE}[8/8] 배포 확인 중...${NC}"
sleep 2

# 로컬에서 헬스 체크
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API 응답 정상${NC}"
else
    echo -e "${YELLOW}⚠️  API가 아직 완전히 시작되지 않았을 수 있습니다${NC}"
fi

# ─── 배포 완료 ──────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}"
cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  ✅ NCP 배포 완료!                                            ║
║                                                                ║
║  🌐 웹사이트: http://223.130.136.16                           ║
║  📊 API 문서: http://223.130.136.16/api/docs                 ║
║  💊 헬스체크: http://223.130.136.16/health                   ║
║                                                                ║
║  📋 유용한 명령어:                                            ║
║     • 로그 확인: journalctl -u goksori -f                     ║
║     • 서비스 상태: systemctl status goksori                   ║
║     • 서비스 재시작: systemctl restart goksori               ║
║     • Nginx 상태: systemctl status nginx                      ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
