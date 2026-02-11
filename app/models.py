"""
SQLAlchemy ORM models for the Stock News & Analysis Platform.

Models:
- StockAnalysisResultDB: Persists stock analysis/speculation results
- SocialContentDB: Persists generated social media content
- StockSectorMappingDB: Persists stock-to-sector mapping for compliance/desensitization

Schema design follows relational database conventions for easy migration to PostgreSQL/MySQL.
"""

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class StockAnalysisResultDB(Base):
    """
    Stock analysis/speculation result persistence.
    
    Replaces JSON file storage in `outputs/stock_analysis/`.
    Stores the complete result of a stock analysis workflow including
    bull/bear arguments, debate dialogue, and controversial conclusions.
    """
    __tablename__ = "stock_analysis_results"

    # Primary key
    id = Column(String(64), primary_key=True, comment="Unique analysis result ID")
    
    # Input data
    topic = Column(Text, nullable=True, comment="Analysis topic (user input)")
    news_titles = Column(Text, nullable=True, comment="JSON array of input news titles")
    
    # Analysis results
    summary = Column(Text, nullable=True, comment="News summary")
    impact_analysis = Column(Text, nullable=True, comment="Impact analysis")
    bull_argument = Column(Text, nullable=True, comment="Bull case argument (aggressive bullish stance)")
    bear_argument = Column(Text, nullable=True, comment="Bear case argument (sharp bearish stance)")
    debate_dialogue = Column(Text, nullable=True, comment="Bull vs Bear debate dialogue")
    controversial_conclusion = Column(Text, nullable=True, comment="Controversial conclusion (clickbait style)")
    stance = Column(String(10), nullable=True, comment="Final stance: bull or bear")
    risk_warning = Column(Text, nullable=True, comment="Risk warning / disclaimer")
    
    # Sentiment context (Phase 3 - nullable for graceful degradation)
    sentiment_context = Column(Text, nullable=True, comment="JSON: Sentiment data snapshot at analysis time")
    
    # Metadata
    cache_hit = Column(Boolean, default=False, comment="Whether result was from cache")
    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        index=True,
        comment="Creation timestamp"
    )

    # Relationships
    social_contents = relationship(
        "SocialContentDB",
        back_populates="source_analysis",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<StockAnalysisResultDB(id={self.id}, topic={self.topic[:30] if self.topic else None}...)>"


class SocialContentDB(Base):
    """
    Social media content persistence.
    
    Replaces JSON file storage in `outputs/social_content/`.
    Stores generated content for various platforms (Xiaohongshu, Weibo, Xueqiu, Zhihu).
    """
    __tablename__ = "social_content"

    # Primary key
    id = Column(String(64), primary_key=True, comment="Unique content ID")
    
    # Platform and type
    platform = Column(String(20), nullable=False, index=True, comment="Target platform: xhs/weibo/xueqiu/zhihu")
    content_type = Column(String(20), nullable=False, comment="Content type: analysis/daily_report")
    
    # Content
    title = Column(Text, nullable=True, comment="Content title (for Xiaohongshu/Xueqiu)")
    body = Column(Text, nullable=False, comment="Content body text")
    tags = Column(Text, nullable=True, comment="JSON array of hashtags")
    image_urls = Column(Text, nullable=True, comment="JSON array of image URLs")
    
    # Compliance/Desensitization
    desensitization_level = Column(
        String(10),
        default="medium",
        comment="Desensitization level: light/medium/heavy/none"
    )
    original_content = Column(Text, nullable=True, comment="Original content before desensitization")
    user_acknowledged_risk = Column(
        Boolean,
        default=False,
        comment="User acknowledged risk when choosing 'none' desensitization"
    )
    
    # Publishing status
    status = Column(String(20), default="draft", comment="Status: draft/published")
    published_at = Column(DateTime, nullable=True, comment="Publication timestamp")
    
    # Foreign key to analysis result
    source_analysis_id = Column(
        String(64),
        ForeignKey("stock_analysis_results.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Related analysis result ID"
    )
    
    # Metadata
    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        index=True,
        comment="Creation timestamp"
    )

    # Relationships
    source_analysis = relationship(
        "StockAnalysisResultDB",
        back_populates="social_contents"
    )

    def __repr__(self) -> str:
        return f"<SocialContentDB(id={self.id}, platform={self.platform}, status={self.status})>"


class StockSectorMappingDB(Base):
    """
    Stock-to-sector mapping for compliance and desensitization.
    
    Replaces JSON file storage in `outputs/compliance/stock_sector_mapping.json`.
    Used to replace stock names with industry descriptions for regulatory compliance.
    """
    __tablename__ = "stock_sector_mapping"

    # Primary key (stock code)
    stock_code = Column(String(10), primary_key=True, comment="Stock code (e.g., 600519)")
    
    # Stock information
    stock_name = Column(String(50), nullable=False, comment="Stock name (e.g., 贵州茅台)")
    
    # Sector/Industry classification
    sector_name = Column(String(50), nullable=True, comment="Sector name (e.g., 白酒)")
    industry_name = Column(String(50), nullable=True, comment="Industry name (e.g., 食品饮料)")
    
    # Desensitization labels
    desensitized_label = Column(
        String(100),
        nullable=True,
        comment="Medium desensitization label (e.g., 某白酒龙头)"
    )
    pinyin_abbr = Column(
        String(10),
        nullable=True,
        comment="Pinyin abbreviation for light desensitization (e.g., GZMT)"
    )
    
    # Ranking
    market_cap_rank = Column(
        Integer,
        nullable=True,
        comment="Market cap rank within industry"
    )
    
    # Metadata
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        comment="Last update timestamp"
    )

    # Create index on stock_name for fast lookup during desensitization
    __table_args__ = (
        Index("ix_stock_sector_mapping_stock_name", "stock_name"),
    )

    def __repr__(self) -> str:
        return f"<StockSectorMappingDB(code={self.stock_code}, name={self.stock_name})>"


class SentimentCommentDB(Base):
    """
    Sentiment comment persistence.

    Stores raw retail investor comments collected from stock discussion forums
    (东方财富股吧, 雪球, 同花顺) with LLM-assigned sentiment labels.
    """
    __tablename__ = "sentiment_comments"

    id = Column(String(64), primary_key=True, comment="Unique comment ID")
    content = Column(Text, nullable=False, comment="Comment text content")
    source_platform = Column(
        String(20), nullable=False, index=True,
        comment="Source platform: eastmoney/xueqiu/10jqka"
    )
    stock_code = Column(
        String(10), nullable=True, index=True,
        comment="Related stock code, NULL for general market discussion"
    )
    author_nickname = Column(String(100), nullable=True, comment="Author nickname")
    published_time = Column(
        DateTime, nullable=False, index=True,
        comment="Comment publish time"
    )
    content_hash = Column(
        String(32), nullable=False, unique=True,
        comment="MD5 hash of content for deduplication"
    )
    sentiment_label = Column(
        String(10), nullable=True,
        comment="Sentiment label: fear/greed/neutral"
    )
    sentiment_score = Column(
        Float, nullable=True,
        comment="Sentiment intensity score (0-100)"
    )
    created_at = Column(
        DateTime, default=datetime.datetime.utcnow,
        comment="Record creation timestamp"
    )

    __table_args__ = (
        Index("ix_sentiment_comments_stock_time", "stock_code", "published_time"),
    )

    def __repr__(self) -> str:
        return f"<SentimentCommentDB(id={self.id}, platform={self.source_platform})>"


class SentimentSnapshotDB(Base):
    """
    Sentiment index snapshot persistence.

    Stores periodic snapshots of the composite fear/greed index
    including sub-scores from mixed data sources.
    """
    __tablename__ = "sentiment_snapshots"

    id = Column(String(64), primary_key=True, comment="Unique snapshot ID")
    stock_code = Column(
        String(10), nullable=True, index=True,
        comment="Stock code, NULL for overall market"
    )
    index_value = Column(
        Float, nullable=False,
        comment="Composite sentiment index (0-100)"
    )
    comment_sentiment_score = Column(
        Float, nullable=True,
        comment="Comment sentiment sub-score (0-100)"
    )
    baidu_vote_score = Column(
        Float, nullable=True,
        comment="Baidu vote sub-score (0-100)"
    )
    akshare_aggregate_score = Column(
        Float, nullable=True,
        comment="AKShare aggregate sub-score (0-100)"
    )
    news_sentiment_score = Column(
        Float, nullable=True,
        comment="News sentiment sub-score (0-100)"
    )
    margin_trading_score = Column(
        Float, nullable=True,
        comment="Margin trading sub-score (0-100)"
    )
    fear_ratio = Column(Float, default=0.0, comment="Fear comment ratio")
    greed_ratio = Column(Float, default=0.0, comment="Greed comment ratio")
    neutral_ratio = Column(Float, default=0.0, comment="Neutral comment ratio")
    sample_count = Column(Integer, default=0, comment="Comment sample count")
    data_source_availability = Column(
        Text, nullable=True,
        comment="JSON: {source_id: bool} availability map"
    )
    label = Column(
        String(20), nullable=False, default="neutral",
        comment="Sentiment label: extreme_fear/fear/neutral/greed/extreme_greed"
    )
    snapshot_time = Column(
        DateTime, nullable=False, index=True,
        comment="Snapshot timestamp"
    )

    __table_args__ = (
        Index("ix_sentiment_snapshots_stock_time", "stock_code", "snapshot_time"),
    )

    def __repr__(self) -> str:
        return f"<SentimentSnapshotDB(id={self.id}, index={self.index_value}, label={self.label})>"
