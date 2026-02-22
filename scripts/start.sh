#!/bin/bash
# 곡소리 매매법 - 앱 시작 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "📢 곡소리 매매법 시작..."
echo "프로젝트 경로: $PROJECT_DIR"

# 1. 환경 설정 확인
if [ ! -f "$PROJECT_DIR/config/.env" ]; then
    echo "⚠️  config/.env 파일이 없습니다."
    echo "설정 파일을 생성합니다..."
    cp "$PROJECT_DIR/config/.env.example" "$PROJECT_DIR/config/.env"
    echo "✅ config/.env 파일이 생성되었습니다."
    echo "📝 파일을 편집하고 다시 실행해주세요."
    exit 1
fi

# 2. Python 버전 확인
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION 사용 중"

# 3. 의존성 설치 (필요시)
if [ "$1" = "--install" ]; then
    echo "📦 의존성 설치 중..."
    cd "$BACKEND_DIR"
    pip install -r requirements.txt --break-system-packages
    echo "✅ 의존성 설치 완료"
fi

# 4. DB 마이그레이션 (선택)
if [ "$1" = "--migrate" ]; then
    echo "🗄️  데이터베이스 마이그레이션 중..."
    cd "$BACKEND_DIR"
    alembic upgrade head
    echo "✅ 마이그레이션 완료"
fi

# 5. 테스트 실행 (선택)
if [ "$1" = "--test" ]; then
    echo "🧪 테스트 실행 중..."
    cd "$BACKEND_DIR"
    python -m pytest tests/ -v
    echo "✅ 테스트 완료"
    exit 0
fi

# 6. 앱 시작
echo ""
echo "🚀 FastAPI 서버 시작 중..."
echo "   접속 주소: http://localhost:8000"
echo ""
cd "$BACKEND_DIR"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
