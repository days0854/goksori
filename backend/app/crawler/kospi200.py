"""
코스피 200 종목 목록 관리
"""
import requests
from bs4 import BeautifulSoup
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StockInfo:
    code: str
    name: str
    market: str = "KOSPI"


KOSPI200_SAMPLE = [
    StockInfo("005930", "삼성전자"),
    StockInfo("000660", "SK하이닉스"),
    StockInfo("207940", "삼성바이오로직스"),
    StockInfo("005380", "현대차"),
    StockInfo("068270", "셀트리온"),
    StockInfo("035420", "NAVER"),
    StockInfo("051910", "LG화학"),
    StockInfo("006400", "삼성SDI"),
    StockInfo("003550", "LG"),
    StockInfo("028260", "삼성물산"),
    StockInfo("012330", "현대모비스"),
    StockInfo("035720", "카카오"),
    StockInfo("055550", "신한지주"),
    StockInfo("373220", "LG에너지솔루션"),
    StockInfo("096770", "SK이노베이션"),
    StockInfo("003490", "대한항공"),
    StockInfo("034730", "SK"),
    StockInfo("105560", "KB금융"),
    StockInfo("086790", "하나금융지주"),
    StockInfo("030200", "KT"),
]


class Kospi200Manager:
    """코스피 200 종목 목록 관리"""

    NAVER_KOSPI200_URL = "https://finance.naver.com/sise/entryJongmok.naver?code=KOSPI200"

    def __init__(self):
        self.stocks: list[StockInfo] = []

    def get_stock_list(self, use_sample: bool = False) -> list[StockInfo]:
        """
        코스피 200 종목 목록 반환
        use_sample=True 이면 하드코딩된 샘플 사용 (개발/테스트용)
        """
        if use_sample:
            return KOSPI200_SAMPLE

        try:
            return self._fetch_from_naver()
        except Exception as e:
            logger.warning(f"코스피200 목록 조회 실패, 샘플 사용: {e}")
            return KOSPI200_SAMPLE

    def _fetch_from_naver(self) -> list[StockInfo]:
        """네이버에서 코스피 200 종목 목록 크롤링"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(self.NAVER_KOSPI200_URL, headers=headers, timeout=10)
        response.encoding = "euc-kr"
        soup = BeautifulSoup(response.text, "lxml")

        stocks = []
        # 네이버 구성종목 테이블 파싱
        for link in soup.find_all("a", href=lambda h: h and "code=" in h):
            code = link["href"].split("code=")[-1].strip()
            name = link.get_text(strip=True)
            if code and name and len(code) == 6 and code.isdigit():
                stocks.append(StockInfo(code=code, name=name))

        logger.info(f"코스피200 {len(stocks)}개 종목 조회")
        return stocks if stocks else KOSPI200_SAMPLE
