"""
곡소리매매법 FastAPI 메인 앱
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from .config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── FastAPI 앱 초기화 ────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="코스피200 종목 감성분석 기반 매매 시그널 서비스",
    version="0.1.0",
    docs_url="/api/docs" if settings.debug else None,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 / 템플릿
BASE_DIR = Path(__file__).parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR / "static")),
    name="static",
)
templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))

# ─── 라우터 등록 ──────────────────────────────────────────────────────────────
from .api import stocks, sentiment, share  # noqa: E402
app.include_router(stocks.router, prefix="/api/stocks", tags=["주식"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["감성분석"])
app.include_router(share.router, prefix="/api/share", tags=["공유"])


# ─── 페이지 라우트 ─────────────────────────────────────────────────────────────
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "곡소리 매매법",
            "adsense_client_id": settings.adsense_client_id,
            "kakao_js_key": settings.kakao_js_key,
        },
    )


@app.get("/stock/{stock_code}")
async def stock_detail(request: Request, stock_code: str):
    return templates.TemplateResponse(
        "stock_detail.html",
        {
            "request": request,
            "stock_code": stock_code,
            "title": f"곡소리 매매법 - {stock_code}",
        },
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name}
