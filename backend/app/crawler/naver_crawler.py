"""
네이버 종목토론방 크롤러
TDD: tests/test_crawler/test_naver_crawler.py 참조
"""
import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CommentData:
    """크롤링된 댓글 데이터 구조"""
    stock_code: str
    source: str
    content: str
    author: str = ""
    likes: int = 0
    dislikes: int = 0
    original_url: str = ""
    crawled_at: datetime = field(default_factory=datetime.now)


class NaverDiscussCrawler:
    """
    네이버 종목토론방 크롤러
    URL: https://finance.naver.com/item/board.naver?code={stock_code}
    """

    BASE_URL = "https://finance.naver.com/item/board.naver"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://finance.naver.com",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    }

    def __init__(self, delay: float = 1.0, max_pages: int = 5):
        """
        Args:
            delay: 요청 간 딜레이 (초) - 서버 부하 방지
            max_pages: 최대 크롤링 페이지 수
        """
        self.delay = delay
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def get_comments(self, stock_code: str, max_comments: int = 100) -> list[CommentData]:
        """
        특정 종목의 토론방 댓글 수집

        Args:
            stock_code: 종목코드 (예: '005930' for 삼성전자)
            max_comments: 최대 수집 댓글 수

        Returns:
            CommentData 리스트
        """
        comments = []
        page = 1

        while len(comments) < max_comments and page <= self.max_pages:
            try:
                page_comments = self._fetch_page(stock_code, page)
                if not page_comments:
                    logger.info(f"{stock_code} 페이지 {page}: 댓글 없음, 중단")
                    break

                comments.extend(page_comments)
                logger.info(f"{stock_code} 페이지 {page}: {len(page_comments)}개 수집")

                page += 1
                time.sleep(self.delay)

            except Exception as e:
                logger.error(f"{stock_code} 페이지 {page} 크롤링 실패: {e}")
                break

        return comments[:max_comments]

    def _fetch_page(self, stock_code: str, page: int) -> list[CommentData]:
        """특정 페이지의 댓글 파싱"""
        url = f"{self.BASE_URL}?code={stock_code}&page={page}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = "euc-kr"
            return self._parse_comments(response.text, stock_code, url)
        except requests.RequestException as e:
            logger.error(f"HTTP 요청 실패 {url}: {e}")
            raise

    def _parse_comments(self, html: str, stock_code: str, url: str) -> list[CommentData]:
        """HTML에서 댓글 파싱"""
        soup = BeautifulSoup(html, "lxml")
        comments = []

        # 네이버 종목토론방 테이블 구조
        table = soup.find("table", class_="type2")
        if not table:
            return comments

        rows = table.find_all("tr", class_=lambda x: x and "bg" in x)

        for row in rows:
            comment = self._parse_row(row, stock_code, url)
            if comment:
                comments.append(comment)

        return comments

    def _parse_row(self, row, stock_code: str, url: str) -> Optional[CommentData]:
        """테이블 행에서 댓글 데이터 추출"""
        try:
            cells = row.find_all("td")
            if len(cells) < 4:
                return None

            # 제목/내용
            title_cell = row.find("td", class_="title")
            if not title_cell:
                return None

            link = title_cell.find("a")
            content = link.get_text(strip=True) if link else title_cell.get_text(strip=True)

            if not content or len(content) < 2:
                return None

            # 작성자
            author_cell = row.find("td", class_="writer")
            author = author_cell.get_text(strip=True) if author_cell else ""

            # 좋아요/싫어요
            likes, dislikes = 0, 0
            td_list = row.find_all("td")
            for td in td_list:
                text = td.get_text(strip=True)
                if text.isdigit():
                    if likes == 0:
                        likes = int(text)
                    elif dislikes == 0:
                        dislikes = int(text)
                        break

            return CommentData(
                stock_code=stock_code,
                source="naver_discuss",
                content=content,
                author=author,
                likes=likes,
                dislikes=dislikes,
                original_url=url,
            )
        except Exception as e:
            logger.warning(f"행 파싱 실패: {e}")
            return None

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
