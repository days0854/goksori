"""
주식 관련 DB 모델
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Stock(Base):
    """코스피 200 종목 마스터 테이블"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True, comment="종목코드 (예: 005930)")
    name = Column(String(100), nullable=False, comment="종목명")
    market = Column(String(10), default="KOSPI", comment="시장구분 (KOSPI/KOSDAQ)")
    sector = Column(String(50), nullable=True, comment="업종")
    is_active = Column(Integer, default=1, comment="활성여부")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    sentiment_scores = relationship("SentimentScore", back_populates="stock")
    comments = relationship("Comment", back_populates="stock")

    def __repr__(self):
        return f"<Stock(code={self.code}, name={self.name})>"


class Comment(Base):
    """수집된 댓글 원본 테이블"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    source = Column(String(50), nullable=False, comment="출처 (naver_discuss/stockplus/etc)")
    content = Column(Text, nullable=False, comment="댓글 내용")
    author = Column(String(100), nullable=True, comment="작성자")
    likes = Column(Integer, default=0, comment="좋아요 수")
    dislikes = Column(Integer, default=0, comment="싫어요 수")
    original_url = Column(Text, nullable=True, comment="원본 URL")
    crawled_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    stock = relationship("Stock", back_populates="comments")
    sentiment = relationship("CommentSentiment", back_populates="comment", uselist=False)

    __table_args__ = (
        Index("idx_comment_stock_source", "stock_id", "source"),
        Index("idx_comment_crawled_at", "crawled_at"),
    )


class CommentSentiment(Base):
    """댓글별 감성분석 결과"""
    __tablename__ = "comment_sentiments"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), unique=True, nullable=False)
    score = Column(Float, nullable=False, comment="감성 점수 (-1.0 ~ 1.0, 양수=긍정)")
    label = Column(String(20), nullable=False, comment="긍정/부정/중립")
    confidence = Column(Float, nullable=True, comment="분석 신뢰도 (0~1)")
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())

    comment = relationship("Comment", back_populates="sentiment")


class SentimentScore(Base):
    """종목별 집계된 감성점수 (4시간마다 업데이트)"""
    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    score = Column(Float, nullable=False, comment="종합 감성 점수 (0~100)")
    positive_count = Column(Integer, default=0, comment="긍정 댓글 수")
    negative_count = Column(Integer, default=0, comment="부정 댓글 수")
    neutral_count = Column(Integer, default=0, comment="중립 댓글 수")
    total_count = Column(Integer, default=0, comment="전체 댓글 수")
    trend = Column(String(10), default="neutral", comment="추세 (up/down/neutral)")
    score_change = Column(Float, default=0.0, comment="이전 대비 변화량")
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stock = relationship("Stock", back_populates="sentiment_scores")

    __table_args__ = (
        Index("idx_sentiment_stock_period", "stock_id", "period_end"),
    )
