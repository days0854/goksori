"""
공유 API
GET /api/share/{stock_code} - 카카오톡 공유용 종목 요약 데이터
"""
from fastapi import APIRouter
import random
from datetime import datetime

router = APIRouter()


@router.get("/{stock_code}")
async def get_share_data(stock_code: str):
    """카카오톡 공유용 종목 데이터"""
    random.seed(hash(stock_code) % 10000)
    score = round(random.uniform(20, 85), 1)
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 45 else "D" if score >= 30 else "E"
    emoji = "🔥" if score >= 70 else "📈" if score >= 55 else "😐" if score >= 45 else "📉" if score >= 30 else "💀"
    trend = "상승" if score > 55 else "하락" if score < 45 else "중립"

    share_text = (
        f"{emoji} 곡소리 매매법 알림\n"
        f"종목: {stock_code}\n"
        f"감성점수: {score}점 ({grade}등급)\n"
        f"추세: {trend}\n"
        f"업데이트: {datetime.now().strftime('%m/%d %H:%M')}\n"
        f"👉 https://goksori.com/stock/{stock_code}"
    )

    return {
        "stock_code": stock_code,
        "score": score,
        "grade": grade,
        "emoji": emoji,
        "trend": trend,
        "share_text": share_text,
        "kakao_share": {
            "title": f"{emoji} {stock_code} 곡소리 감성점수: {score}점",
            "description": f"등급: {grade} | 추세: {trend} | {datetime.now().strftime('%m/%d %H:%M')} 기준",
            "link_url": f"https://goksori.com/stock/{stock_code}",
            "image_url": f"https://goksori.com/static/images/og_{stock_code}.png",
        },
    }
