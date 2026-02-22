# 곡소리 매매법 - 개발 환경 설정 가이드

## 📋 요구사항
- Python 3.10+
- PostgreSQL 12+ (선택: 개발 시 메모리 DB 사용 가능)
- Node.js 16+ (프론트엔드 빌드 선택)

## 🚀 빠른 시작 (5분)

### 1. 저장소 클론 및 의존성 설치
```bash
cd goksori/backend
pip install -r requirements.txt --break-system-packages
```

### 2. 환경 설정
```bash
# config/.env 파일 생성 (예시에서 복사)
cp config/.env.example config/.env

# .env 파일 편집 - 필수 설정
# DATABASE_URL=postgresql://user:password@localhost:5432/goksori_db
# SECRET_KEY=your-secret-key-here
# DART_API_KEY=optional
```

### 3. 앱 실행
```bash
# 개발 모드 (hot reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 브라우저에서 열기
```
http://localhost:8000
```

## 📝 TDD 테스트 실행

### 감성분석 모듈 테스트
```bash
python -m pytest backend/tests/test_sentiment/test_analyzer.py -v
```

### 크롤러 모듈 테스트
```bash
python -m pytest backend/tests/test_crawler/test_naver_crawler.py -v
```

### 모든 테스트 실행
```bash
python -m pytest backend/tests/ -v
```

## 🗄️ 데이터베이스 마이그레이션

### 1. Alembic 초기화 (최초 1회)
```bash
cd backend
alembic init -t async migrations
```

### 2. 마이그레이션 파일 자동 생성
```bash
alembic revision --autogenerate -m "Initial migration"
```

### 3. 마이그레이션 적용
```bash
alembic upgrade head
```

## 🔧 주요 파일 구조

```
goksori/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 앱 진입점
│   │   ├── config.py         # 설정 관리
│   │   ├── api/
│   │   │   ├── stocks.py     # 주식 데이터 API
│   │   │   ├── sentiment.py  # 감성분석 API
│   │   │   └── share.py      # 공유 API
│   │   ├── crawler/          # 크롤러 모듈
│   │   ├── sentiment/        # 감성분석 엔진
│   │   ├── models/           # DB 모델
│   │   └── db/               # DB 세션
│   ├── tests/                # TDD 테스트
│   └── requirements.txt
├── frontend/
│   ├── templates/            # HTML 페이지
│   └── static/               # CSS, JS, 이미지
├── config/                   # 환경 설정
└── docs/                     # 문서
```

## 🎯 API 엔드포인트

### 주식 관련
- `GET /api/stocks/` - 코스피200 목록 (페이지네이션, 정렬, 검색)
- `GET /api/stocks/{code}` - 특정 종목 상세

### 감성분석
- `POST /api/sentiment/analyze` - 텍스트 감성분석
- `GET /api/sentiment/{code}/history` - 종목 점수 추이

### 공유
- `GET /api/share/{code}` - 카카오톡 공유 데이터

## 🌐 프론트엔드 개발

### 핫 리로드 (선택)
프론트엔드는 정적 파일로 제공되므로, 별도의 빌드 도구 필요 없음.
CSS/JS 수정 후 브라우저에서 `F5` 또는 `Ctrl+Shift+R` 로 강제 새로고침

### 구조
- `frontend/templates/` - Jinja2 HTML 템플릿
- `frontend/static/css/` - 스타일시트
- `frontend/static/js/` - JavaScript (Chart.js, Kakao API 연동)

## 🔒 보안 체크리스트

- [ ] SECRET_KEY 변경 (프로덕션)
- [ ] DATABASE_URL 환경변수 설정
- [ ] CORS origin 설정 변경 (프로덕션: 특정 도메인만)
- [ ] API 레이트 제한 추가
- [ ] HTTPS 설정
- [ ] 크롤링 User-Agent 설정
- [ ] API 인증 (JWT) 추가 검토

## 📦 배포 (네이버 클라우드)

### 1. 서버 생성
```bash
# Ubuntu 22.04 서버 생성
ssh ubuntu@your-server-ip
sudo apt update && sudo apt install python3.10 python3-pip postgresql-14
```

### 2. 앱 배포
```bash
git clone <repo-url>
cd goksori/backend
pip install -r requirements.txt
cp config/.env.example config/.env
# .env 파일 수정
```

### 3. Systemd 서비스 설정
```bash
# /etc/systemd/system/goksori.service 생성
sudo cp scripts/goksori.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable goksori
sudo systemctl start goksori
```

### 4. Nginx 리버스 프록시
```nginx
server {
    listen 80;
    server_name goksori.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 트러블슈팅

### "Module not found" 에러
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:/path/to/goksori/backend"
```

### 포트 이미 사용 중
```bash
# 다른 포트로 실행
python -m uvicorn app.main:app --port 8001
```

### DB 연결 실패
```bash
# 환경변수 확인
echo $DATABASE_URL

# PostgreSQL 상태 확인
psql -U user -d goksori_db -c "SELECT 1;"
```

## 📚 추가 리소스
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/)
- [Chart.js](https://www.chartjs.org/)
- [Kakao 공유하기](https://developers.kakao.com/docs/latest/ko/message/js-sdk)
