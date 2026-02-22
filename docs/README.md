# 곡소리 매매법 (Goksori Trading Signals)

## 프로젝트 개요
코스피 200 종목에 대한 네이버 종목토론방 및 외부 주식 관련 사이트의 댓글을 수집하여
긍정/부정 감성 분석 결과를 시각화하는 웹사이트

## 목표 시스템 구성
```
[데이터 수집] → [감성 분석] → [DB 저장] → [API 제공] → [웹 시각화]
     4시간마다                  PostgreSQL    FastAPI       HTML/JS
```

## 기술 스택
- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Database**: PostgreSQL (네이버 클라우드 예정)
- **Crawler**: BeautifulSoup4, requests, APScheduler
- **Sentiment**: KoNLPy / transformers (KoBERT)
- **Frontend**: HTML5, CSS3, Vanilla JS (Chart.js)
- **Server**: Naver Cloud Platform
- **Monetization**: Google AdSense

## 프로젝트 구조
```
goksori/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 라우터
│   │   ├── crawler/      # 크롤링 모듈
│   │   ├── sentiment/    # 감성분석 모듈
│   │   ├── models/       # DB 모델 (SQLAlchemy)
│   │   ├── db/           # DB 연결 설정
│   │   └── utils/        # 공통 유틸리티
│   └── tests/            # TDD 테스트
│       ├── test_crawler/
│       ├── test_sentiment/
│       └── test_api/
├── frontend/
│   ├── static/           # CSS, JS, 이미지
│   └── templates/        # Jinja2 HTML 템플릿
├── config/               # 환경 설정
├── scripts/              # 배포/마이그레이션 스크립트
└── docs/                 # 문서
```

## 개발 로드맵 (1주일 TDD 스프린트)
| 일차 | 담당 | 작업 |
|------|------|------|
| Day 1 | 웹사이트 구축자 | UI 프로토타입 (메인 화면) |
| Day 2 | 데이터 아키텍처 | DB 스키마, 모델 설계 |
| Day 2-3 | 크롤링 개발자 | 네이버 토론방 크롤러 |
| Day 3-4 | 감성분석 개발자 | 한국어 감성분석 파이프라인 |
| Day 4-5 | 웹사이트 구축자 | FastAPI + 동적 화면 연동 |
| Day 5-6 | 디자이너 | UI/UX 고도화, 모바일 대응 |
| Day 6-7 | 보안관리자 | 보안 점검, 배포 설정 |

## 에이전트 역할
- **오케스트레이터**: 전체 진행 조율, 스프린트 관리
- **크롤링 툴 개발자**: 네이버/외부사이트 크롤러
- **웹사이트 구축자**: FastAPI + 프론트엔드
- **디자이너**: UI/UX, 반응형 디자인
- **데이터 아키텍처**: DB 설계, 외부 데이터 연동 (DART 공시)
- **보안관리자**: 크롤링 보안, API 보안, 서버 보안

## 실행 방법
```bash
# 개발 환경 설정
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 테스트 실행
pytest tests/ -v
```
