"""
🎯 Portfolio Management Models
Advanced portfolio tracking, valuation, and performance analytics
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON, 
    ForeignKey, Index, CheckConstraint, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base

class ConditionGrade(str, Enum):
    """Card condition grades"""
    MINT = "mint"
    NEAR_MINT = "near_mint"
    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    GRADED = "graded"

class TransactionType(str, Enum):
    """Portfolio transaction types"""
    BUY = "buy"
    SELL = "sell"
    TRADE_IN = "trade_in"
    TRADE_OUT = "trade_out"
    GIFT_RECEIVED = "gift_received"
    GIFT_GIVEN = "gift_given"
    ADJUSTMENT = "adjustment"

class PortfolioStatus(str, Enum):
    """Portfolio status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class Portfolio(Base):
    """User portfolio container"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Owner information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Portfolio details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=PortfolioStatus.ACTIVE.value, index=True)
    
    # Configuration
    is_public = Column(Boolean, default=False, index=True)
    is_default = Column(Boolean, default=False)
    currency = Column(String(3), default="USD")  # ISO currency code
    
    # Portfolio metrics (cached for performance)
    total_value = Column(Numeric(12, 2), default=0, nullable=False)
    total_cost = Column(Numeric(12, 2), default=0, nullable=False)
    total_profit_loss = Column(Numeric(12, 2), default=0, nullable=False)
    profit_loss_percentage = Column(Float, default=0, nullable=False)
    
    # Inventory counts
    total_cards = Column(Integer, default=0, nullable=False)
    unique_cards = Column(Integer, default=0, nullable=False)
    
    # Performance tracking
    best_performer_id = Column(Integer, ForeignKey("portfolio_items.id"), nullable=True)
    worst_performer_id = Column(Integer, ForeignKey("portfolio_items.id"), nullable=True)
    
    # Analysis metadata
    last_valuation = Column(DateTime, nullable=True)
    valuation_confidence = Column(Float, nullable=True)  # 0-1 scale
    
    # Display preferences
    display_preferences = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    items = relationship("PortfolioItem", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("PortfolioTransaction", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_portfolio_user_status", "user_id", "status"),
        Index("idx_portfolio_public", "is_public"),
        Index("idx_portfolio_value", "total_value"),
        Index("idx_portfolio_default", "user_id", "is_default"),
    )

class PortfolioItem(Base):
    """Individual items in a portfolio"""
    __tablename__ = "portfolio_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Portfolio association
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Product information
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Item details
    quantity = Column(Integer, nullable=False, default=1)
    condition_grade = Column(String(20), nullable=False, default=ConditionGrade.NEAR_MINT.value)
    
    # Grading information (for graded cards)
    grading_company = Column(String(50), nullable=True)  # PSA, BGS, CGC, etc.
    grade_score = Column(String(10), nullable=True)      # 10, 9.5, etc.
    certification_number = Column(String(100), nullable=True, unique=True)
    
    # Cost basis
    purchase_price = Column(Numeric(10, 2), nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    purchase_source = Column(String(100), nullable=True)
    
    # Current valuation
    current_value = Column(Numeric(10, 2), nullable=True)
    last_valued_at = Column(DateTime, nullable=True)
    valuation_source = Column(String(50), nullable=True)
    
    # Performance metrics
    profit_loss = Column(Numeric(10, 2), nullable=True)
    profit_loss_percentage = Column(Float, nullable=True)
    
    # Item metadata
    notes = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)  # ["investment", "collection", "trade"]
    
    # Storage and location
    storage_location = Column(String(200), nullable=True)
    is_for_sale = Column(Boolean, default=False, index=True)
    asking_price = Column(Numeric(10, 2), nullable=True)
    
    # Insurance and protection
    is_insured = Column(Boolean, default=False)
    insurance_value = Column(Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="items")
    product = relationship("Product")
    transactions = relationship("PortfolioTransaction", back_populates="item")
    
    # Indexes
    __table_args__ = (
        Index("idx_item_portfolio_product", "portfolio_id", "product_id"),
        Index("idx_item_condition", "condition_grade"),
        Index("idx_item_graded", "grading_company", "grade_score"),
        Index("idx_item_value", "current_value"),
        Index("idx_item_for_sale", "is_for_sale"),
        CheckConstraint("quantity > 0", name="check_positive_quantity"),
        CheckConstraint("purchase_price >= 0", name="check_non_negative_price"),
    )

class PortfolioTransaction(Base):
    """Portfolio transaction history"""
    __tablename__ = "portfolio_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Transaction identification
    transaction_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Portfolio and item association
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("portfolio_items.id"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    
    # Transaction metadata
    transaction_date = Column(DateTime, nullable=False, index=True)
    source = Column(String(100), nullable=True)  # Where the transaction occurred
    
    # Fees and costs
    fees = Column(Numeric(10, 2), default=0)
    shipping_cost = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    
    # Market context
    market_price_at_time = Column(Numeric(10, 2), nullable=True)
    condition_grade = Column(String(20), nullable=True)
    
    # Notes and documentation
    notes = Column(Text, nullable=True)
    receipt_url = Column(String(500), nullable=True)
    
    # Counterparty information (for trades)
    counterparty = Column(String(200), nullable=True)
    trade_details = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    item = relationship("PortfolioItem", back_populates="transactions")
    product = relationship("Product")
    
    # Indexes
    __table_args__ = (
        Index("idx_transaction_portfolio_date", "portfolio_id", "transaction_date"),
        Index("idx_transaction_type_date", "transaction_type", "transaction_date"),
        Index("idx_transaction_amount", "total_amount"),
        CheckConstraint("quantity != 0", name="check_non_zero_quantity"),
        CheckConstraint("price_per_unit >= 0", name="check_non_negative_unit_price"),
    )

class PortfolioSnapshot(Base):
    """Portfolio value snapshots for performance tracking"""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Portfolio association
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Snapshot timing
    snapshot_date = Column(DateTime, nullable=False, index=True)
    snapshot_type = Column(String(20), nullable=False)  # "daily", "weekly", "monthly", "manual"
    
    # Portfolio metrics at snapshot time
    total_value = Column(Numeric(12, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)
    total_profit_loss = Column(Numeric(12, 2), nullable=False)
    profit_loss_percentage = Column(Float, nullable=False)
    
    # Inventory metrics
    total_cards = Column(Integer, nullable=False)
    unique_cards = Column(Integer, nullable=False)
    
    # Performance metrics
    daily_change = Column(Numeric(10, 2), nullable=True)
    daily_change_percentage = Column(Float, nullable=True)
    
    # Market comparison
    market_index_value = Column(Float, nullable=True)  # If we have a market index
    relative_performance = Column(Float, nullable=True)
    
    # Top performers at snapshot time
    top_gainers = Column(JSONB, nullable=True)
    top_losers = Column(JSONB, nullable=True)
    
    # Asset allocation
    allocation_by_set = Column(JSONB, nullable=True)
    allocation_by_rarity = Column(JSONB, nullable=True)
    allocation_by_price_range = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")
    
    # Indexes
    __table_args__ = (
        Index("idx_snapshot_portfolio_date", "portfolio_id", "snapshot_date"),
        Index("idx_snapshot_type_date", "snapshot_type", "snapshot_date"),
        Index("idx_snapshot_value", "total_value"),
        Index("idx_snapshot_performance", "profit_loss_percentage"),
    )

class Watchlist(Base):
    """User watchlists for tracking products of interest"""
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Owner information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Watchlist details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    is_public = Column(Boolean, default=False, index=True)
    is_default = Column(Boolean, default=False)
    
    # Alert settings
    price_alert_enabled = Column(Boolean, default=True)
    price_change_threshold = Column(Float, default=5.0)  # Percentage
    notification_frequency = Column(String(20), default="daily")
    
    # Display preferences
    sort_order = Column(String(50), default="name")
    display_preferences = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_watchlist_user", "user_id"),
        Index("idx_watchlist_public", "is_public"),
        Index("idx_watchlist_default", "user_id", "is_default"),
    )

class WatchlistItem(Base):
    """Items in user watchlists"""
    __tablename__ = "watchlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Watchlist association
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False, index=True)
    
    # Product information
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Watch configuration
    target_price = Column(Numeric(10, 2), nullable=True)
    price_alert_type = Column(String(20), nullable=True)  # "below", "above", "change"
    
    # Priority and notes
    priority = Column(String(10), default="medium")  # "low", "medium", "high"
    notes = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)
    
    # Price tracking
    price_when_added = Column(Numeric(10, 2), nullable=True)
    highest_price_seen = Column(Numeric(10, 2), nullable=True)
    lowest_price_seen = Column(Numeric(10, 2), nullable=True)
    
    # Alert history
    last_alert_sent = Column(DateTime, nullable=True)
    alert_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")
    product = relationship("Product")
    
    # Indexes
    __table_args__ = (
        Index("idx_watchlist_item_watchlist_product", "watchlist_id", "product_id"),
        Index("idx_watchlist_item_priority", "priority"),
        Index("idx_watchlist_item_target_price", "target_price"),
    )

class CollectionGoal(Base):
    """User collection goals and tracking"""
    __tablename__ = "collection_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Owner information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Goal definition
    goal_type = Column(String(50), nullable=False)  # "complete_set", "rarity_collection", "value_target"
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Target criteria
    target_set = Column(String(255), nullable=True, index=True)
    target_rarity = Column(String(50), nullable=True)
    target_value = Column(Numeric(12, 2), nullable=True)
    target_count = Column(Integer, nullable=True)
    
    # Progress tracking
    current_count = Column(Integer, default=0)
    current_value = Column(Numeric(12, 2), default=0)
    completion_percentage = Column(Float, default=0)
    
    # Timeline
    target_date = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_achieved = Column(Boolean, default=False, index=True)
    achieved_at = Column(DateTime, nullable=True)
    
    # Motivation and rewards
    reward_description = Column(Text, nullable=True)
    milestone_rewards = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="collection_goals")
    
    # Indexes
    __table_args__ = (
        Index("idx_goal_user_active", "user_id", "is_active"),
        Index("idx_goal_type", "goal_type"),
        Index("idx_goal_set", "target_set"),
        Index("idx_goal_completion", "completion_percentage"),
        CheckConstraint("completion_percentage >= 0 AND completion_percentage <= 100", 
                       name="check_completion_percentage_range"),
    )

class PerformanceMetric(Base):
    """Portfolio performance metrics and analytics"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Portfolio association
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Metric details
    metric_name = Column(String(100), nullable=False, index=True)
    metric_category = Column(String(50), nullable=False)  # "return", "risk", "allocation"
    
    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # "daily", "weekly", "monthly", "yearly"
    
    # Metric values
    value = Column(Float, nullable=False)
    benchmark_value = Column(Float, nullable=True)
    relative_value = Column(Float, nullable=True)  # Value relative to benchmark
    
    # Additional context
    data_points = Column(Integer, nullable=True)
    confidence_level = Column(Float, nullable=True)
    calculation_method = Column(String(100), nullable=True)
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio")
    
    # Indexes
    __table_args__ = (
        Index("idx_metric_portfolio_period", "portfolio_id", "period_end"),
        Index("idx_metric_name_period", "metric_name", "period_type"),
        Index("idx_metric_value", "value"),
    )