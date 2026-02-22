#!/bin/bash
################################################################################
#                     곡소리 매매법 - NCP 자동 배포 스크립트
#
# 사용법:
#   ./scripts/deploy-ncp.sh        (대화형 모드)
#   ./scripts/deploy-ncp.sh auto   (자동모드 - 설정 파일 필요)
################################################################################

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

# 스크립트 시작
clear
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   🚀 곡소리 매매법 - NCP 자동 배포 스크립트                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ─── 1. 배포 설정 ───────────────────────────────────────────────────────────

CONFIG_FILE="scripts/.ncp-deploy.conf"

if [ "$1" == "auto" ] && [ -f "$CONFIG_FILE" ]; then
    log_info "자동 모드: $CONFIG_FILE 사용"
    source "$CONFIG_FILE"
else
    log_info "대화형 모드 - NCP 배포 정보 입력"
    echo ""

    # NCP 서버 정보
    echo -e "${YELLOW}┌─ NCP 서버 정보 ─────────────────────────┐${NC}"
    read -p "  NCP 서버 IP 주소: " NCP_SERVER_IP
    read -p "  서버 포트 (기본 22): " NCP_SERVER_PORT
    NCP_SERVER_PORT=${NCP_SERVER_PORT:-22}

    echo ""
    echo "  접속 방법:"
    echo "    1) SSH 키 (.pem 파일)"
    echo "    2) 비밀번호"
    read -p "  선택 (1 또는 2): " ACCESS_METHOD

    if [ "$ACCESS_METHOD" == "1" ]; then
        read -p "  SSH 개인키 경로 (.pem): " NCP_SSH_KEY
        NCP_SSH_USER="root"
        NCP_ACCESS_TYPE="key"
    else
        read -sp "  서버 비밀번호: " NCP_SERVER_PASSWORD
        echo ""
        NCP_SSH_USER="root"
        NCP_ACCESS_TYPE="password"
    fi

    # DB 정보
    echo ""
    echo -e "${YELLOW}┌─ PostgreSQL DB 정보 ──────────────────┐${NC}"
    read -p "  DB 호스트: " DB_HOST
    read -p "  DB 포트 (기본 5432): " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    read -p "  DB 이름: " DB_NAME
    read -p "  DB 사용자명 (기본 postgres): " DB_USER
    DB_USER=${DB_USER:-postgres}
    read -sp "  DB 비밀번호: " DB_PASSWORD
    echo ""

    # 도메인
    echo ""
    read -p "  도메인 또는 IP (HTTP 접속): " DOMAIN

    # 설정 저장
    log_info "설정 저장 중..."
    mkdir -p scripts
    cat > "$CONFIG_FILE" << EOF
# NCP 배포 설정 (자동 생성됨)
NCP_SERVER_IP="$NCP_SERVER_IP"
NCP_SERVER_PORT="$NCP_SERVER_PORT"
NCP_SSH_USER="$NCP_SSH_USER"
NCP_ACCESS_TYPE="$NCP_ACCESS_TYPE"
NCP_SSH_KEY="$NCP_SSH_KEY"
NCP_SERVER_PASSWORD="$NCP_SERVER_PASSWORD"

DB_HOST="$DB_HOST"
DB_PORT="$DB_PORT"
DB_NAME="$DB_NAME"
DB_USER="$DB_USER"
DB_PASSWORD="$DB_PASSWORD"

DOMAIN="$DOMAIN"
EOF
    log_success "설정 저장됨: $CONFIG_FILE"
fi

# ─── 2. NCP 서버 접속 정보 검증 ─────────────────────────────────────────────

log_info "NCP 서버 접속 정보 검증 중..."

if [ "$NCP_ACCESS_TYPE" == "key" ]; then
    if [ ! -f "$NCP_SSH_KEY" ]; then
        log_error "SSH 키 파일을 찾을 수 없습니다: $NCP_SSH_KEY"
    fi
    SSH_CMD="ssh -i $NCP_SSH_KEY -p $NCP_SERVER_PORT"
    SSHPASS_CMD=""
else
    SSH_CMD="sshpass -p '$NCP_SERVER_PASSWORD' ssh -p $NCP_SERVER_PORT"
fi

# ─── 3. NCP 서버 연결 테스트 ─────────────────────────────────────────────────

log_info "NCP 서버 연결 테스트 중..."
if eval "$SSH_CMD -o ConnectTimeout=5 $NCP_SSH_USER@$NCP_SERVER_IP 'echo OK'" > /dev/null 2>&1; then
    log_success "NCP 서버 연결 성공!"
else
    log_error "NCP 서버에 접속할 수 없습니다. IP, 포트, 접속 방법을 확인하세요."
fi

# ─── 4. DB 연결 테스트 ──────────────────────────────────────────────────────

log_info "PostgreSQL DB 연결 테스트 중..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_success "DB 연결 성공!"
else
    log_error "DB에 접속할 수 없습니다. 호스트, 포트, 자격증명을 확인하세요."
fi

# ─── 5. NCP 서버에 배포 ──────────────────────────────────────────────────────

log_info "배포 패키지 준비 중..."

# 로컬에서 프로젝트 패킹
TEMP_DIR=$(mktemp -d)
tar -czf "$TEMP_DIR/goksori.tar.gz" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='venv' \
    --exclude='.env' \
    backend/ frontend/ docs/ scripts/ config/

log_success "배포 패키지 생성됨: $TEMP_DIR/goksori.tar.gz"

# SCP로 파일 전송
log_info "파일을 NCP 서버로 전송 중..."

if [ "$NCP_ACCESS_TYPE" == "key" ]; then
    scp -i "$NCP_SSH_KEY" -P "$NCP_SERVER_PORT" "$TEMP_DIR/goksori.tar.gz" \
        "$NCP_SSH_USER@$NCP_SERVER_IP:/tmp/goksori.tar.gz"
else
    sshpass -p "$NCP_SERVER_PASSWORD" scp -P "$NCP_SERVER_PORT" "$TEMP_DIR/goksori.tar.gz" \
        "$NCP_SSH_USER@$NCP_SERVER_IP:/tmp/goksori.tar.gz"
fi

log_success "파일 전송 완료!"

# ─── 6. NCP 서버에서 배포 스크립트 실행 ──────────────────────────────────────

log_info "NCP 서버에서 배포 진행 중..."

DEPLOY_SCRIPT=$(cat << 'DEPLOY_EOF'
#!/bin/bash
set -e

# 설정
PROJECT_DIR="/home/goksori"
PYTHON_VERSION="3.10"

echo "📦 패키지 해제 중..."
cd /tmp
tar -xzf goksori.tar.gz
mkdir -p $PROJECT_DIR
cp -r backend frontend docs scripts config $PROJECT_DIR/

echo "🔧 시스템 의존성 설치 중..."
apt-get update
apt-get install -y python3.10 python3-pip git nginx postgresql-client

echo "🐍 Python 가상환경 설정 중..."
cd $PROJECT_DIR/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️  환경 설정 작성 중..."
cat > config/.env << 'ENV_EOF'
DATABASE_URL=postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}
APP_NAME=곡소리매매법
APP_ENV=production
DEBUG=false
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
CRAWL_INTERVAL_HOURS=4
MAX_COMMENTS_PER_STOCK=100
ENV_EOF

echo "🔐 Systemd 서비스 설정 중..."
cat > /etc/systemd/system/goksori.service << 'SYSTEMD_EOF'
[Unit]
Description=Goksori Trading Signal Service
After=network.target postgresql.service

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

echo "🌐 Nginx 리버스 프록시 설정 중..."
cat > /etc/nginx/sites-available/goksori << 'NGINX_EOF'
server {
    listen 80;
    server_name {DOMAIN};
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
NGINX_EOF

ln -sf /etc/nginx/sites-available/goksori /etc/nginx/sites-enabled/goksori
nginx -t
systemctl restart nginx

echo "🚀 곡소리 서비스 시작 중..."
systemctl start goksori
sleep 2
systemctl status goksori --no-pager

echo "✅ NCP 배포 완료!"
echo ""
echo "접속 주소: http://{DOMAIN}"
echo "API 문서: http://{DOMAIN}/api/docs"
echo ""
echo "로그 확인: journalctl -u goksori -f"
DEPLOY_EOF
)

# 배포 스크립트에 설정값 주입
DEPLOY_SCRIPT="${DEPLOY_SCRIPT//\{DB_USER\}/$DB_USER}"
DEPLOY_SCRIPT="${DEPLOY_SCRIPT//\{DB_PASSWORD\}/$DB_PASSWORD}"
DEPLOY_SCRIPT="${DEPLOY_SCRIPT//\{DB_HOST\}/$DB_HOST}"
DEPLOY_SCRIPT="${DEPLOY_SCRIPT//\{DB_PORT\}/$DB_PORT}"
DEPLOY_SCRIPT="${DEPLOY_SCRIPT//\{DB_NAME\}/$DB_NAME}"
DEPLOY_SCRIPT="${DEPLOY_SCRIPT//\{DOMAIN\}/$DOMAIN}"

# NCP 서버에서 배포 스크립트 실행
eval "$SSH_CMD $NCP_SSH_USER@$NCP_SERVER_IP 'bash -s'" << EOF
$DEPLOY_SCRIPT
EOF

# ─── 7. 최종 확인 ──────────────────────────────────────────────────────────

log_info "배포 후 최종 확인 중..."

# 서비스 상태 확인
log_info "서비스 상태 확인..."
eval "$SSH_CMD $NCP_SSH_USER@$NCP_SERVER_IP 'systemctl status goksori --no-pager'"

# API 헬스 체크
log_info "API 헬스 체크..."
sleep 2
if curl -s "http://$DOMAIN/health" > /dev/null 2>&1; then
    log_success "API 응답 정상!"
else
    log_warning "API가 아직 응답하지 않습니다. 몇 초 더 기다려주세요."
fi

# ─── 8. 배포 완료 ──────────────────────────────────────────────────────────

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  ✅ NCP 배포 완료!                                            ║"
echo "║                                                                ║"
echo "║  🌐 접속 주소: http://$DOMAIN                                "
echo "║  📊 API 문서: http://$DOMAIN/api/docs                        "
echo "║  💻 SSH 접속: ssh -i KEY.pem root@$NCP_SERVER_IP             "
echo "║                                                                ║"
echo "║  📋 로그 확인:                                                ║"
echo "║     journalctl -u goksori -f                                  ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 정리
rm -rf "$TEMP_DIR"
log_success "배포 스크립트 종료"
