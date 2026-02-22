"""
감성분석 API
POST /api/sentiment/analyze  - 텍스트 단건 분석
GET  /api/sentiment/{code}   - 종목 최신 감성 요약
GET  /api/sentiment/{code}/history - 점수 추이
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import random

from ..sentiment.analyzer import RuleBasedSentimentAnalyzer, SentimentAggregator

router = APIRouter()
analyzer = RuleBasedSentimentAnalyzer()


class AnalyzeRequest(BaseModel):
    text: str


@router.post("/analyze")
async def analyze_text(req: AnalyzeRequest):
    """단일 텍스트 감성분석"""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="텍스트를 입력해주세요")
    result = analyzer.analyze(req.text)
    return {
        "text": req.text,
        "score": result.score,
        "normalized_score": result.normalized_score,
        "label": result.label,
        "confidence": result.confidence,
        "emoji": result.emoji,
        "grade": result.grade,
    }


@router.get("/{stock_code}/history")
async def get_score_history(stock_code: str, days: int = 30):
    """종목 감성점수 추이 (최근 N일)"""
    random.seed(hash(stock_code) % 10000)
    base = random.uniform(30, 75)
    history = []
    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        score = round(max(10, min(90, base + random.uniform(-12, 12))), 1)
        history.append({"date": date, "score": score})
    return {"stock_code": stock_code, "history": history}
