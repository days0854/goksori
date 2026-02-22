"""
주식 목록 API
GET /api/stocks/       - 코스피200 전체 목록 + 최신 감성점수
GET /api/stocks/{code} - 특정 종목 상세 (댓글, 공시, 차트)
"""
from fastapi import APIRouter, Query
from typing import Optional
import random
from datetime import datetime

router = APIRouter()


def _mock_sentiment_data(stock_code: str, stock_name: str) -> dict:
    """
    개발용 목업 데이터 (실제 DB 연결 전까지 사용)
    실제 구현 시 DB 쿼리로 대체
    """
    # 종목코드를 시드로 사용해 일관된 랜덤값 생성
    random.seed(hash(stock_code) % 10000)
    score = random.uniform(20, 85)
    pos = random.randint(10, 80)
    neg = random.randint(5, 60)
    neu = random.randint(5, 40)
    total = pos + neg + neu
    trend = "up" if score > 55 else "down" if score < 45 else "neutral"

    return {
        "code": stock_code,
        "name": stock_name,
        "score": round(score, 1),
        "grade": "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 45 else "D" if score >= 30 else "E",
        "emoji": "🔥" if score >= 70 else "📈" if score >= 55 else "😐" if score >= 45 else "📉" if score >= 30 else "💀",
        "trend": trend,
        "score_change": round(random.uniform(-10, 10), 1),
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": neu,
        "total_count": total,
        "updated_at": datetime.now().isoformat(),
    }


# 코스피200 샘플 목록
SAMPLE_STOCKS = [
    ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("207940", "삼성바이오로직스"),
    ("005380", "현대차"), ("068270", "셀트리온"), ("035420", "NAVER"),
    ("051910", "LG화학"), ("006400", "삼성SDI"), ("003550", "LG"),
    ("028260", "삼성물산"), ("012330", "현대모비스"), ("035720", "카카오"),
    ("055550", "신한지주"), ("373220", "LG에너지솔루션"), ("096770", "SK이노베이션"),
    ("003490", "대한항공"), ("034730", "SK"), ("105560", "KB금융"),
    ("086790", "하나금융지주"), ("030200", "KT"), ("017670", "SK텔레콤"),
    ("032830", "삼성생명"), ("009150", "삼성전기"), ("018260", "삼성에스디에스"),
    ("066570", "LG전자"), ("000270", "기아"), ("011200", "HMM"),
    ("316140", "우리금융지주"), ("015760", "한국전력"), ("032640", "LG유플러스"),
    ("000100", "유한양행"), ("011170", "롯데케미칼"), ("024110", "기업은행"),
    ("078930", "GS"), ("036570", "엔씨소프트"), ("010950", "S-Oil"),
    ("000810", "삼성화재"), ("011790", "SKC"), ("009540", "한국조선해양"),
    ("042660", "한화오션"), ("047050", "포스코인터내셔널"), ("000120", "CJ대한통운"),
    ("010140", "삼성중공업"), ("021240", "코웨이"), ("161390", "한국타이어앤테크놀로지"),
    ("004020", "현대제철"), ("005945", "NH투자증권"), ("034020", "두산에너빌리티"),
    ("009900", "OCI"), ("029780", "삼성카드"),
]


@router.get("/")
async def get_stocks(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    sort: str = Query("score_desc", pattern="^(score_desc|score_asc|name|trend_up|trend_down)$"),
    search: Optional[str] = None,
):
    """
    코스피200 종목 목록 + 감성점수
    - page/size: 페이지네이션
    - sort: 정렬 기준
    - search: 종목명/코드 검색
    """
    stocks = [_mock_sentiment_data(code, name) for code, name in SAMPLE_STOCKS]

    # 검색 필터
    if search:
        search = search.strip().lower()
        stocks = [s for s in stocks if search in s["name"].lower() or search in s["code"]]

    # 정렬
    if sort == "score_desc":
        stocks.sort(key=lambda x: x["score"], reverse=True)
    elif sort == "score_asc":
        stocks.sort(key=lambda x: x["score"])
    elif sort == "name":
        stocks.sort(key=lambda x: x["name"])
    elif sort == "trend_up":
        stocks = [s for s in stocks if s["trend"] == "up"] + \
                 [s for s in stocks if s["trend"] != "up"]
    elif sort == "trend_down":
        stocks = [s for s in stocks if s["trend"] == "down"] + \
                 [s for s in stocks if s["trend"] != "down"]

    # 페이지네이션
    total = len(stocks)
    start = (page - 1) * size
    end = start + size
    paginated = stocks[start:end]

    return {
        "total": total,
        "page": page,
        "size": size,
        "stocks": paginated,
    }


@router.get("/{stock_code}")
async def get_stock_detail(stock_code: str):
    """특정 종목 상세 정보"""
    # 종목명 찾기
    stock_name = next((name for code, name in SAMPLE_STOCKS if code == stock_code), stock_code)

    base_data = _mock_sentiment_data(stock_code, stock_name)

    # 최근 댓글 목업
    random.seed(hash(stock_code) % 10000 + 1)
    mock_comments = [
        {
            "id": i,
            "content": f"{'긍정 의견: 이 종목 좋아보임' if i % 3 == 0 else '부정 의견: 조심해야함' if i % 3 == 1 else '중립: 지켜봐야할듯'}",
            "author": f"투자자{i:03d}",
            "likes": random.randint(0, 50),
            "sentiment": "positive" if i % 3 == 0 else "negative" if i % 3 == 1 else "neutral",
            "source": "naver_discuss",
            "crawled_at": datetime.now().isoformat(),
        }
        for i in range(1, 21)
    ]

    # 최근 7일 점수 추이 목업
    score_history = []
    base_score = base_data["score"]
    for i in range(7, 0, -1):
        score_history.append({
            "date": f"2026-02-{20-i:02d}",
            "score": round(max(10, min(90, base_score + random.uniform(-15, 15))), 1),
        })

    return {
        **base_data,
        "comments": mock_comments,
        "score_history": score_history,
        "sources": ["naver_discuss"],
        "dart_url": f"https://dart.fss.or.kr/dsearch/main.do?rcpNo=&textCrpCik={stock_code}",
    }
