#!/bin/bash
################################################################################
#          곡소리 매매법 - NCP 원격 배포 완전 자동화 스크립트
#          로컬에서 실행: bash complete-deploy.sh
################################################################################

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# NCP 서버 정보
NCP_HOST="223.130.136.16"
NCP_USER="root"
NCP_PASS="U4*G!@m*86Te7cu"
NCP_PORT="22"

echo -e "${BLUE}"
cat << 'BANNER'
╔════════════════════════════════════════════════════════════════╗
║   🚀 곡소리 매매법 - NCP 원격 배포 완전 자동화                ║
╚════════════════════════════════════════════════════════════════╝
BANNER
echo -e "${NC}"

# ─── Step 1: 프로젝트 압축 ──────────────────────────────────────────────────

echo -e "${BLUE}[1/4] 프로젝트 압축 중...${NC}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARBALL="$PROJECT_DIR/goksori-deploy.tar.gz"

cd "$PROJECT_DIR"
tar --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='goksori-deploy.tar.gz' \
    -czf "$TARBALL" backend frontend docs scripts config

if [ -f "$TARBALL" ]; then
    SIZE=$(du -h "$TARBALL" | cut -f1)
    echo -e "${GREEN}✅ 압축 완료 ($SIZE)${NC}"
else
    echo -e "${RED}❌ 압축 실패${NC}"
    exit 1
fi

# ─── Step 2: 서버 접속 및 파일 업로드 ──────────────────────────────────────

echo -e "${BLUE}[2/4] 서버에 파일 업로드 중...${NC}"

# sshpass 설치 확인
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}❌ 에러: sshpass가 설치되어 있지 않습니다.${NC}"
    echo ""
    echo "설치 방법:"
    echo "  Ubuntu/Debian: sudo apt-get install -y sshpass"
    echo "  macOS: brew install sshpass"
    echo "  CentOS/RHEL: sudo yum install -y sshpass"
    echo ""
    echo "또는 NCP 서버에 SSH 키 기반 인증 설정 후 sshpass 없이 진행할 수 있습니다."
    exit 1
fi

# SSH 호스트 키 확인 비활성화하고 파일 업로드
export SSHPASS="$NCP_PASS"
sshpass -e scp -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -P "$NCP_PORT" \
    "$TARBALL" "$NCP_USER@$NCP_HOST:/tmp/goksori-deploy.tar.gz"

echo -e "${GREEN}✅ 파일 업로드 완료${NC}"

# ─── Step 3: 배포 스크립트 생성 및 실행 ──────────────────────────────────────

echo -e "${BLUE}[3/4] 서버에서 배포 스크립트 실행 중...${NC}"

# 배포 스크립트
DEPLOY_SCRIPT='
#!/bin/bash
set -e

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"

echo -e "${BLUE}[시작] NCP 서버 배포${NC}"

# 1. 시스템 업데이트
echo -e "${BLUE}[1/7] 시스템 패키지 업데이트...${NC}"
apt-get update > /dev/null 2>&1 || true
apt-get install -y python3.10 python3-pip git nginx curl > /dev/null 2>&1
echo -e "${GREEN}✅ 완료${NC}"

# 2. 프로젝트 디렉토리 준비
echo -e "${BLUE}[2/7] 프로젝트 파일 추출...${NC}"
rm -rf /home/goksori
mkdir -p /home/goksori
cd /home/goksori
tar -xzf /tmp/goksori-deploy.tar.gz
echo -e "${GREEN}✅ 완료${NC}"

# 3. Python 가상환경
echo -e "${BLUE}[3/7] Python 환경 구성...${NC}"
cd /home/goksori/backend
python3.10 -m venv venv > /dev/null 2>&1
source venv/bin/activate
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✅ 완료${NC}"

# 4. 환경 설정
echo -e "${BLUE}[4/7] 환경 설정 파일 생성...${NC}"
mkdir -p config
SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
cat > config/.env << EOF
DATABASE_URL=postgresql://days:Project0423!@projectabout-001-8tq0.vpc.nclouddb.com:5432/goksori_db
APP_NAME=곡소리매매법
APP_ENV=production
DEBUG=false
SECRET_KEY=$SECRET
CRAWL_INTERVAL_HOURS=4
MAX_COMMENTS_PER_STOCK=100
REQUEST_DELAY_SECONDS=1
EOF
echo -e "${GREEN}✅ 완료${NC}"

# 5. Systemd 서비스
echo -e "${BLUE}[5/7] Systemd 서비스 등록...${NC}"
cat > /etc/systemd/system/goksori.service << "EOF"
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
EOF
systemctl daemon-reload
systemctl enable goksori > /dev/null 2>&1
echo -e "${GREEN}✅ 완료${NC}"

# 6. Nginx 설정
echo -e "${BLUE}[6/7] Nginx 리버스 프록시 설정...${NC}"
cat > /etc/nginx/sites-available/goksori << "EOF"
server {
    listen 80;
    server_name _;
    client_max_body_size 10M;

    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }
}
EOF
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/goksori /etc/nginx/sites-enabled/goksori
nginx -t > /dev/null 2>&1
systemctl restart nginx
echo -e "${GREEN}✅ 완료${NC}"

# 7. 서비스 시작
echo -e "${BLUE}[7/7] 곡소리 서비스 시작...${NC}"
systemctl start goksori
sleep 3

if systemctl is-active --quiet goksori; then
    echo -e "${GREEN}✅ 완료${NC}"
else
    echo -e "${RED}❌ 실패${NC}"
    journalctl -u goksori -n 20
    exit 1
fi

echo ""
echo -e "${GREEN}"
cat << "COMPLETE"
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  ✅ NCP 배포 완료!                                            ║
║                                                                ║
║  🌐 웹사이트: http://223.130.136.16                           ║
║  📊 API 문서: http://223.130.136.16/api/docs                 ║
║  💊 헬스체크: curl http://127.0.0.1:8000/health             ║
║                                                                ║
║  📋 로그 확인:                                                ║
║     journalctl -u goksori -f                                  ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
COMPLETE
echo -e "${NC}"
'

# 배포 스크립트 실행
sshpass -e ssh -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -p "$NCP_PORT" "$NCP_USER@$NCP_HOST" \
    "bash -c '$DEPLOY_SCRIPT'" || {
    echo -e "${RED}❌ 배포 스크립트 실행 실패${NC}"
    exit 1
}

echo -e "${GREEN}✅ 배포 스크립트 실행 완료${NC}"

# ─── Step 4: 배포 완료 확인 ──────────────────────────────────────────────────

echo -e "${BLUE}[4/4] 배포 확인 중...${NC}"
sleep 2

# 헬스 체크
if curl -s "http://$NCP_HOST/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 헬스 체크 성공${NC}"
else
    echo -e "${YELLOW}⚠️  헬스 체크 대기 중... (몇 초 더 소요될 수 있음)${NC}"
    sleep 5
    if curl -s "http://$NCP_HOST/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 헬스 체크 성공${NC}"
    else
        echo -e "${YELLOW}⚠️  아직 시작 중입니다. 잠시 후 확인하세요.${NC}"
    fi
fi

# ─── 배포 완료 ──────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}"
cat << 'COMPLETE'
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  ✅ 모든 배포 단계 완료!                                      ║
║                                                                ║
║  🌐 웹사이트 접속:                                            ║
║     http://223.130.136.16                                     ║
║                                                                ║
║  📊 API 문서:                                                 ║
║     http://223.130.136.16/api/docs                           ║
║                                                                ║
║  💡 다음 단계:                                                ║
║     1. 웹사이트에 접속해서 정상 작동 확인                    ║
║     2. SSH로 접속해서 로그 확인: journalctl -u goksori -f   ║
║     3. 필요시 SSL 인증서 설정 (Let's Encrypt)               ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
COMPLETE
echo -e "${NC}"

# 정리
echo -e "${BLUE}정리 중...${NC}"
rm -f "$TARBALL"
echo -e "${GREEN}✅ 완료${NC}"

echo ""
echo "🎉 배포가 완료되었습니다!"
