"""
감성분석 모듈 TDD 테스트
실행: pytest backend/tests/test_sentiment/ -v
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from app.sentiment.analyzer import (
    RuleBasedSentimentAnalyzer,
    SentimentAggregator,
    SentimentLabel,
    SentimentResult,
)


@pytest.fixture
def analyzer():
    return RuleBasedSentimentAnalyzer()


class TestRuleBasedSentimentAnalyzer:

    def test_strong_positive_text(self, analyzer):
        result = analyzer.analyze("삼성전자 급등 예상! 상한가 갈듯 매수 기회")
        assert result.label == SentimentLabel.POSITIVE
        assert result.score > 0.5
        assert result.normalized_score > 60

    def test_strong_negative_text(self, analyzer):
        result = analyzer.analyze("이거 폭락할듯 손절 각 사기 종목임")
        assert result.label == SentimentLabel.NEGATIVE
        assert result.score < -0.5
        assert result.normalized_score < 40

    def test_neutral_text(self, analyzer):
        result = analyzer.analyze("오늘 거래량 어떻게 됨?")
        assert result.label == SentimentLabel.NEUTRAL

    def test_empty_text(self, analyzer):
        result = analyzer.analyze("")
        assert result.label == SentimentLabel.NEUTRAL
        assert result.normalized_score == 50.0

    def test_negation_reversal(self, analyzer):
        pos_result = analyzer.analyze("급등할 것 같다")
        neg_result = analyzer.analyze("급등 안 할 것 같다")
        assert pos_result.score > neg_result.score

    def test_normalized_score_range(self, analyzer):
        texts = ["급등 폭등 상한가 대박", "폭락 급락 하한가 손절", "오늘 주가 어때요"]
        for text in texts:
            result = analyzer.analyze(text)
            assert 0.0 <= result.normalized_score <= 100.0

    def test_emoji_property(self, analyzer):
        high_result = SentimentResult(score=0.8, label=SentimentLabel.POSITIVE,
                                       confidence=0.9, normalized_score=90.0)
        low_result = SentimentResult(score=-0.8, label=SentimentLabel.NEGATIVE,
                                      confidence=0.9, normalized_score=10.0)
        assert high_result.emoji == "🔥"
        assert low_result.emoji == "💀"

    def test_grade_property(self, analyzer):
        a_result = SentimentResult(score=0.9, label=SentimentLabel.POSITIVE,
                                    confidence=1.0, normalized_score=85.0)
        assert a_result.grade == "A"

        e_result = SentimentResult(score=-0.9, label=SentimentLabel.NEGATIVE,
                                    confidence=1.0, normalized_score=15.0)
        assert e_result.grade == "E"


class TestSentimentAggregator:

    def test_empty_input(self):
        result = SentimentAggregator.aggregate([])
        assert result["score"] == 50.0
        assert result["total_count"] == 0
        assert result["trend"] == "neutral"

    def test_all_positive(self, analyzer):
        texts = ["급등예상", "매수기회", "상한가갈듯"]
        results = [analyzer.analyze(t) for t in texts]
        agg = SentimentAggregator.aggregate(results)
        assert agg["score"] > 55
        assert agg["trend"] == "up"
        assert agg["positive_count"] > 0

    def test_all_negative(self, analyzer):
        texts = ["폭락", "손절각", "사기종목"]
        results = [analyzer.analyze(t) for t in texts]
        agg = SentimentAggregator.aggregate(results)
        assert agg["score"] < 45
        assert agg["trend"] == "down"

    def test_mixed_results(self, analyzer):
        texts = ["급등예상", "폭락할듯", "그냥그래"]
        results = [analyzer.analyze(t) for t in texts]
        agg = SentimentAggregator.aggregate(results)
        assert 0 <= agg["score"] <= 100
        assert agg["total_count"] == 3
