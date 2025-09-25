"""
🎯 Analytics & Intelligence Models
Advanced models for market analytics, trends, and user intelligence
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base

class TrendType(str, Enum):
    """Market trend types"""
    PRICE = "price"
    VOLUME = "volume"
    SENTIMENT = "sentiment"
    POPULARITY = "popularity"

class TrendDirection(str, Enum):
    """Trend directions"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    VOLATILE = "volatile"

class AlertType(str, Enum):
    """Price alert types"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE = "price_change"
    VOLUME_SPIKE = "volume_spike"
    NEW_LISTING = "new_listing"

class AlertStatus(str, Enum):
    """Alert statuses"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"

class MarketTrend(Base):
    """Market trend analysis and tracking"""
    __tablename__ = "market_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Trend identification
    trend_type = Column(String(50), nullable=False, index=True)
    trend_direction = Column(String(20), nullable=False)
    
    # Product association
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    set_name = Column(String(255), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    
    # Trend metrics
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    strength = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Price data
    start_price = Column(Float, nullable=True)
    end_price = Column(Float, nullable=True)
    peak_price = Column(Float, nullable=True)
    trough_price = Column(Float, nullable=True)
    
    # Volume and activity
    volume_change = Column(Float, nullable=True)
    listing_count = Column(Integer, nullable=True)
    seller_count = Column(Integer, nullable=True)
    
    # Analysis metadata
    data_points = Column(Integer, nullable=False, default=0)
    sources = Column(JSON, nullable=True)  # ["tcgplayer", "ebay"]
    analysis_method = Column(String(100), nullable=True)
    
    # Additional insights
    market_cap_impact = Column(Float, nullable=True)
    correlation_factors = Column(JSONB, nullable=True)
    external_events = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="trends")
    
    # Indexes
    __table_args__ = (
        Index("idx_trend_product_date", "product_id", "start_date"),
        Index("idx_trend_type_direction", "trend_type", "trend_direction"),
        Index("idx_trend_strength", "strength"),
        CheckConstraint("strength >= 0 AND strength <= 1", name="check_strength_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="check_confidence_range"),
    )

class PriceAlert(Base):
    """User price alerts and notifications"""
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User association
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Alert configuration
    alert_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default=AlertStatus.ACTIVE.value, index=True)
    
    # Product targeting
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    product_name = Column(String(255), nullable=True)
    set_name = Column(String(255), nullable=True)
    keywords = Column(JSONB, nullable=True)  # For flexible matching
    
    # Alert conditions
    target_price = Column(Float, nullable=True)
    condition_type = Column(String(20), nullable=True)  # "above", "below", "change"
    percentage_change = Column(Float, nullable=True)
    
    # Trigger configuration
    min_condition_rating = Column(String(10), nullable=True)
    max_price_limit = Column(Float, nullable=True)
    notification_frequency = Column(String(20), default="immediate")  # "immediate", "daily", "weekly"
    
    # Notification settings
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    webhook_url = Column(String(500), nullable=True)
    
    # Alert metadata
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    auto_disable_after_trigger = Column(Boolean, default=False)
    
    # Additional configuration
    custom_message = Column(Text, nullable=True)
    alert_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="price_alerts")
    product = relationship("Product")
    
    # Indexes
    __table_args__ = (
        Index("idx_alert_user_status", "user_id", "status"),
        Index("idx_alert_product_active", "product_id", "status"),
        Index("idx_alert_type_status", "alert_type", "status"),
        Index("idx_alert_last_checked", "last_checked"),
    )

class AnalyticsEvent(Base):
    """User analytics and behavior tracking"""
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event identification
    event_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # User context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    anonymous_id = Column(String(100), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    
    # Product context
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    product_name = Column(String(255), nullable=True)
    set_name = Column(String(255), nullable=True)
    
    # Event properties
    properties = Column(JSONB, nullable=True)
    value = Column(Float, nullable=True)  # Monetary or numeric value
    
    # Technical context
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    referrer = Column(String(500), nullable=True)
    page_url = Column(String(500), nullable=True)
    
    # Geographic context
    country = Column(String(10), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User")
    product = relationship("Product")
    
    # Indexes
    __table_args__ = (
        Index("idx_event_user_time", "user_id", "timestamp"),
        Index("idx_event_type_time", "event_type", "timestamp"),
        Index("idx_event_product_time", "product_id", "timestamp"),
        Index("idx_event_session", "session_id", "timestamp"),
    )

class SearchQuery(Base):
    """Search query tracking and analytics"""
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Query details
    query_text = Column(String(500), nullable=False, index=True)
    normalized_query = Column(String(500), nullable=True, index=True)
    query_hash = Column(String(64), nullable=True, index=True)  # For deduplication
    
    # User context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # Search metadata
    search_type = Column(String(50), nullable=True)  # "product", "set", "card"
    filters_applied = Column(JSONB, nullable=True)
    sort_order = Column(String(50), nullable=True)
    
    # Results metadata
    total_results = Column(Integer, nullable=True)
    results_returned = Column(Integer, nullable=True)
    results_clicked = Column(Integer, default=0)
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)
    data_sources = Column(JSONB, nullable=True)  # Which APIs were used
    
    # User interaction
    clicked_results = Column(JSONB, nullable=True)  # Product IDs clicked
    conversion_value = Column(Float, nullable=True)  # If led to transaction
    
    # Geographic and technical context
    country = Column(String(10), nullable=True)
    device_type = Column(String(20), nullable=True)  # "mobile", "desktop", "tablet"
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_search_query_text", "query_text"),
        Index("idx_search_user_time", "user_id", "timestamp"),
        Index("idx_search_hash_time", "query_hash", "timestamp"),
        Index("idx_search_results", "total_results"),
    )

class UserBehavior(Base):
    """User behavior patterns and preferences"""
    __tablename__ = "user_behaviors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User identification
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Behavior category
    behavior_type = Column(String(100), nullable=False, index=True)
    behavior_name = Column(String(200), nullable=False)
    
    # Frequency and patterns
    frequency_score = Column(Float, nullable=False, default=0.0)  # 0-1 scale
    recency_score = Column(Float, nullable=False, default=0.0)   # 0-1 scale
    intensity_score = Column(Float, nullable=False, default=0.0) # 0-1 scale
    
    # Time patterns
    preferred_time_of_day = Column(String(20), nullable=True)  # "morning", "afternoon", "evening"
    preferred_day_of_week = Column(String(20), nullable=True)
    session_duration_avg = Column(Integer, nullable=True)  # Minutes
    
    # Product preferences
    favorite_sets = Column(JSONB, nullable=True)
    favorite_rarities = Column(JSONB, nullable=True)
    price_range_preference = Column(JSONB, nullable=True)  # {"min": 0, "max": 100}
    
    # Search patterns
    common_search_terms = Column(JSONB, nullable=True)
    search_frequency = Column(Float, nullable=True)  # Searches per day
    
    # Engagement metrics
    page_views_per_session = Column(Float, nullable=True)
    bounce_rate = Column(Float, nullable=True)  # 0-1 scale
    conversion_rate = Column(Float, nullable=True)  # 0-1 scale
    
    # Predictive scores
    churn_risk_score = Column(Float, nullable=True)  # 0-1 scale
    lifetime_value_score = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)
    
    # Analysis metadata
    data_points_count = Column(Integer, default=0)
    confidence_score = Column(Float, nullable=True)
    last_analysis = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="behaviors")
    
    # Indexes
    __table_args__ = (
        Index("idx_behavior_user_type", "user_id", "behavior_type"),
        Index("idx_behavior_frequency", "frequency_score"),
        Index("idx_behavior_engagement", "engagement_score"),
        Index("idx_behavior_churn_risk", "churn_risk_score"),
    )

class MarketInsight(Base):
    """Market insights and intelligence reports"""
    __tablename__ = "market_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Insight identification
    insight_type = Column(String(100), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=False)
    
    # Scope and targeting
    scope = Column(String(50), nullable=False)  # "global", "set", "product", "category"
    target_product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    target_set = Column(String(255), nullable=True, index=True)
    target_category = Column(String(100), nullable=True, index=True)
    
    # Insight metrics
    confidence_level = Column(Float, nullable=False)  # 0-1 scale
    impact_score = Column(Float, nullable=False)     # 0-1 scale
    urgency_level = Column(String(20), nullable=False)  # "low", "medium", "high", "critical"
    
    # Financial impact
    price_impact_min = Column(Float, nullable=True)
    price_impact_max = Column(Float, nullable=True)
    volume_impact = Column(Float, nullable=True)
    
    # Data and evidence
    supporting_data = Column(JSONB, nullable=True)
    data_sources = Column(JSONB, nullable=True)
    analysis_method = Column(String(100), nullable=True)
    
    # Content
    detailed_analysis = Column(Text, nullable=True)
    recommendations = Column(JSONB, nullable=True)
    risk_factors = Column(JSONB, nullable=True)
    
    # Publication and lifecycle
    is_published = Column(Boolean, default=False, index=True)
    published_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # User targeting
    target_user_tiers = Column(JSONB, nullable=True)  # ["free", "gold", "platinum"]
    min_subscription_level = Column(String(20), nullable=True)
    
    # Performance tracking
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    bookmark_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product")
    
    # Indexes
    __table_args__ = (
        Index("idx_insight_type_published", "insight_type", "is_published"),
        Index("idx_insight_impact_confidence", "impact_score", "confidence_level"),
        Index("idx_insight_urgency", "urgency_level"),
        Index("idx_insight_expires", "expires_at"),
    )

class RecommendationEngine(Base):
    """ML-powered recommendation tracking"""
    __tablename__ = "recommendation_engines"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Engine identification
    engine_name = Column(String(100), nullable=False, unique=True, index=True)
    engine_version = Column(String(20), nullable=False)
    engine_type = Column(String(50), nullable=False)  # "collaborative", "content", "hybrid"
    
    # Configuration
    algorithm = Column(String(100), nullable=False)
    hyperparameters = Column(JSONB, nullable=True)
    feature_set = Column(JSONB, nullable=True)
    
    # Performance metrics
    accuracy_score = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Training data
    training_samples = Column(Integer, nullable=True)
    validation_samples = Column(Integer, nullable=True)
    feature_count = Column(Integer, nullable=True)
    
    # Status and lifecycle
    is_active = Column(Boolean, default=False, index=True)
    is_production = Column(Boolean, default=False, index=True)
    last_trained = Column(DateTime, nullable=True)
    next_training = Column(DateTime, nullable=True)
    
    # Usage statistics
    recommendation_count = Column(Integer, default=0)
    click_through_rate = Column(Float, nullable=True)
    conversion_rate = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_engine_active", "is_active"),
        Index("idx_engine_production", "is_production"),
        Index("idx_engine_performance", "accuracy_score"),
    )