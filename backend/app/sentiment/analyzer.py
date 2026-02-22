"""
한국어 주식 댓글 감성분석 모듈
경량화된 룰 기반 + (선택적) 딥러닝 혼합 방식
토큰 절약을 위해 규칙 기반을 기본으로 사용
"""
import re
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    score: float          # -1.0 (매우 부정) ~ +1.0 (매우 긍정)
    label: SentimentLabel
    confidence: float     # 0.0 ~ 1.0
    normalized_score: float  # 0 ~ 100 (웹 표시용)

    @property
    def emoji(self) -> str:
        if self.normalized_score >= 70:
            return "🔥"
        elif self.normalized_score >= 55:
            return "📈"
        elif self.normalized_score >= 45:
            return "😐"
        elif self.normalized_score >= 30:
            return "📉"
        else:
            return "💀"

    @property
    def grade(self) -> str:
        """A~E 등급"""
        if self.normalized_score >= 80:
            return "A"
        elif self.normalized_score >= 65:
            return "B"
        elif self.normalized_score >= 45:
            return "C"
        elif self.normalized_score >= 30:
            return "D"
        else:
            return "E"


# ─── 한국어 주식 감성 사전 ─────────────────────────────────────────────────────

STRONG_POSITIVE = [
    "급등", "폭등", "상한가", "대박", "매수", "강추", "올라간다", "오른다",
    "ㄱㄷ", "기대", "호재", "실적개선", "흑자전환", "신고가", "돌파",
    "저평가", "매집", "수급좋음", "외인매수", "기관매수",
]
WEAK_POSITIVE = [
    "좋아", "좋은", "상승", "오를것", "긍정", "기회", "저점", "반등",
    "회복", "괜찮", "성장", "수익", "배당", "안전", "추천",
]
STRONG_NEGATIVE = [
    "급락", "폭락", "하한가", "손절", "망했", "팔아라", "폭탄", "쓰레기",
    "사기", "악재", "적자", "파산", "부도", "관리종목", "상장폐지", "쓰레기",
    "먹튀", "작전", "개잡주",
]
WEAK_NEGATIVE = [
    "하락", "내려", "부정", "걱정", "위험", "손실", "불안", "힘들",
    "나쁜", "문제", "우려", "주의", "조심",
]
NEGATION_WORDS = ["안", "못", "없", "아니", "절대", "결코", "전혀"]


class RuleBasedSentimentAnalyzer:
    """
    규칙 기반 한국어 주식 감성분석기
    - 빠르고 가볍게 동작
    - 딥러닝 모델 대비 정확도 낮지만 인프라 비용 없음
    """

    def __init__(self):
        self.strong_pos = set(STRONG_POSITIVE)
        self.weak_pos = set(WEAK_POSITIVE)
        self.strong_neg = set(STRONG_NEGATIVE)
        self.weak_neg = set(WEAK_NEGATIVE)
        self.negations = set(NEGATION_WORDS)

    def analyze(self, text: str) -> SentimentResult:
        """
        텍스트 감성분석

        Returns:
            SentimentResult
        """
        if not text or not text.strip():
            return SentimentResult(
                score=0.0,
                label=SentimentLabel.NEUTRAL,
                confidence=0.5,
                normalized_score=50.0,
            )

        text = self._preprocess(text)
        score = self._calculate_score(text)
        label = self._score_to_label(score)
        confidence = min(abs(score) * 1.5 + 0.3, 1.0)
        normalized = self._normalize_score(score)

        return SentimentResult(
            score=score,
            label=label,
            confidence=confidence,
            normalized_score=normalized,
        )

    def _preprocess(self, text: str) -> str:
        """전처리: 특수문자 제거, 소문자화"""
        text = re.sub(r"[^\w\s가-힣]", " ", text)
        return text.strip()

    def _calculate_score(self, text: str) -> float:
        """감성 점수 계산"""
        score = 0.0

        # 부정어 체크
        has_negation = any(neg in text for neg in self.negations)
        negation_factor = -0.7 if has_negation else 1.0

        for word in self.strong_pos:
            if word in text:
                score += 0.8 * negation_factor
        for word in self.weak_pos:
            if word in text:
                score += 0.3 * negation_factor
        for word in self.strong_neg:
            if word in text:
                score -= 0.8
        for word in self.weak_neg:
            if word in text:
                score -= 0.3

        # 이모티콘 보정
        if "ㅋㅋ" in text or "ㅎㅎ" in text:
            score += 0.1
        if "ㅠㅠ" in text or "ㅜㅜ" in text:
            score -= 0.1

        return max(-1.0, min(1.0, score))

    def _score_to_label(self, score: float) -> SentimentLabel:
        if score > 0.15:
            return SentimentLabel.POSITIVE
        elif score < -0.15:
            return SentimentLabel.NEGATIVE
        return SentimentLabel.NEUTRAL

    def _normalize_score(self, score: float) -> float:
        """-1~1 범위를 0~100으로 변환"""
        return round((score + 1) / 2 * 100, 1)


class SentimentAggregator:
    """여러 댓글의 감성점수를 종목 단위로 집계"""

    @staticmethod
    def aggregate(results: list[SentimentResult]) -> dict:
        """
        Args:
            results: 댓글별 감성분석 결과 리스트

        Returns:
            종목 집계 결과 딕셔너리
        """
        if not results:
            return {
                "score": 50.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "total_count": 0,
                "trend": "neutral",
            }

        pos = sum(1 for r in results if r.label == SentimentLabel.POSITIVE)
        neg = sum(1 for r in results if r.label == SentimentLabel.NEGATIVE)
        neu = sum(1 for r in results if r.label == SentimentLabel.NEUTRAL)
        total = len(results)

        # 가중 평균 점수 (신뢰도 반영)
        weighted_sum = sum(r.normalized_score * r.confidence for r in results)
        weight_total = sum(r.confidence for r in results)
        avg_score = weighted_sum / weight_total if weight_total > 0 else 50.0

        trend = "up" if avg_score > 55 else "down" if avg_score < 45 else "neutral"

        return {
            "score": round(avg_score, 1),
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "total_count": total,
            "trend": trend,
        }
