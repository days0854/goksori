"""
네이버 크롤러 TDD 테스트
실행: pytest backend/tests/test_crawler/ -v
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from app.crawler.naver_crawler import NaverDiscussCrawler, CommentData


# 테스트용 샘플 HTML
SAMPLE_HTML = """
<html>
<body>
<table class="type2">
<tr class="bg">
  <td class="title"><a href="/item/board_read.naver?code=005930&nid=1">삼성전자 급등 예상합니다</a></td>
  <td class="writer">투자자1</td>
  <td>5</td><td>1</td>
</tr>
<tr class="bg">
  <td class="title"><a href="/item/board_read.naver?code=005930&nid=2">지금 매수 기회인듯</a></td>
  <td class="writer">투자자2</td>
  <td>3</td><td>0</td>
</tr>
</table>
</body>
</html>
"""


@pytest.fixture
def crawler():
    return NaverDiscussCrawler(delay=0, max_pages=1)


class TestNaverDiscussCrawler:

    def test_crawler_initialization(self, crawler):
        assert crawler.delay == 0
        assert crawler.max_pages == 1
        assert crawler.BASE_URL == "https://finance.naver.com/item/board.naver"

    def test_parse_comments_from_html(self, crawler):
        comments = crawler._parse_comments(SAMPLE_HTML, "005930", "http://test.url")
        assert len(comments) == 2
        assert comments[0].stock_code == "005930"
        assert comments[0].source == "naver_discuss"
        assert "삼성전자" in comments[0].content

    def test_parse_comment_data_structure(self, crawler):
        comments = crawler._parse_comments(SAMPLE_HTML, "005930", "http://test.url")
        comment = comments[0]
        assert isinstance(comment, CommentData)
        assert comment.stock_code == "005930"
        assert comment.source == "naver_discuss"
        assert len(comment.content) > 0

    def test_empty_html_returns_empty_list(self, crawler):
        comments = crawler._parse_comments("<html></html>", "005930", "url")
        assert comments == []

    def test_comment_data_has_required_fields(self, crawler):
        comments = crawler._parse_comments(SAMPLE_HTML, "005930", "http://test.url")
        for comment in comments:
            assert hasattr(comment, "stock_code")
            assert hasattr(comment, "source")
            assert hasattr(comment, "content")
            assert hasattr(comment, "author")
            assert hasattr(comment, "likes")
            assert hasattr(comment, "dislikes")
            assert hasattr(comment, "crawled_at")

    @patch("app.crawler.naver_crawler.requests.Session.get")
    def test_get_comments_with_mock(self, mock_get, crawler):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_HTML
        mock_response.encoding = "euc-kr"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        comments = crawler.get_comments("005930", max_comments=10)
        assert len(comments) <= 10
        assert all(isinstance(c, CommentData) for c in comments)

    def test_context_manager(self):
        with NaverDiscussCrawler(delay=0) as crawler:
            assert crawler is not None

    def test_max_comments_limit(self, crawler):
        # 한 페이지에 2개 댓글 있는 HTML로 3개만 요청하면 2개만 반환
        with patch.object(crawler, "_fetch_page") as mock_fetch:
            sample_comments = [
                CommentData("005930", "naver_discuss", f"댓글{i}")
                for i in range(2)
            ]
            mock_fetch.return_value = sample_comments
            result = crawler.get_comments("005930", max_comments=1)
            assert len(result) <= 1
