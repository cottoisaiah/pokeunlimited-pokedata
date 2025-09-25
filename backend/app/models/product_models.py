"""
🎴 Product Models
Comprehensive Pokemon TCG product catalog with multi-source integration
"""

from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, Text, 
    DECIMAL, ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.database import Base


class Product(Base):
    """Core Pokemon TCG product model"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic product information
    name = Column(String(500), nullable=False, index=True)
    set_name = Column(String(255), index=True)
    series = Column(String(100), index=True)
    number = Column(String(20))  # Card number in set
    rarity = Column(String(50), index=True)
    
    # Product classification
    product_type = Column(String(50), default="Cards", index=True)  # Cards, Sealed Products
    condition = Column(String(20), default="Near Mint")  # NM, LP, MP, HP, DMG
    printing = Column(String(50))  # 1st Edition, Unlimited, Shadowless
    language = Column(String(10), default="English")
    
    # Visual information
    image_url = Column(String(1000))
    image_urls = Column(JSON)  # Multiple image URLs
    
    # External IDs for cross-platform integration
    tcgplayer_id = Column(Integer, unique=True, index=True)
    ebay_product_id = Column(String(50), unique=True, index=True)
    odoo_product_id = Column(Integer, unique=True, index=True)
    pokemontcg_io_id = Column(String(50), unique=True, index=True)
    
    # Product metadata
    description = Column(Text)
    flavor_text = Column(Text)
    artist = Column(String(255))
    
    # Set information
    set_id = Column(Integer, ForeignKey("product_sets.id"), nullable=True, index=True)
    set_code = Column(String(20))
    set_release_date = Column(DateTime(timezone=True))
    set_total_cards = Column(Integer)
    
    # Card-specific attributes (for individual cards)
    hp = Column(Integer)
    pokemon_type = Column(String(50))  # Fire, Water, etc.
    stage = Column(String(50))  # Basic, Stage 1, Stage 2
    retreat_cost = Column(Integer)
    weakness = Column(String(50))
    resistance = Column(String(50))
    
    # Sealed product attributes (for booster boxes, etc.)
    cards_per_pack = Column(Integer)
    packs_per_box = Column(Integer)
    msrp = Column(DECIMAL(10, 2))
    
    # Status and tracking
    is_active = Column(Boolean, default=True)
    is_tracked = Column(Boolean, default=True)  # Whether to track pricing
    is_featured = Column(Boolean, default=False)
    
    # Popularity and demand metrics
    popularity_score = Column(Integer, default=0)
    demand_index = Column(DECIMAL(5, 2))
    investment_grade = Column(String(1))  # A, B, C, D rating
    
    # Custom attributes (flexible JSON storage)
    attributes = Column(JSON)
    product_metadata = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_price_update = Column(DateTime(timezone=True))
    
    # Relationships
    set = relationship("ProductSet", back_populates="products")
    pricing_data = relationship("ProductPricing", back_populates="product")
    price_history = relationship("PriceHistory", back_populates="product")
    portfolio_items = relationship("PortfolioItem", back_populates="product")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_product_set_rarity', 'set_name', 'rarity'),
        Index('idx_product_type_condition', 'product_type', 'condition'),
        Index('idx_product_popularity', 'popularity_score', 'demand_index'),
    )


class ProductPricing(Base):
    """Current pricing data aggregated from multiple sources"""
    __tablename__ = "product_pricing"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # TCGPlayer pricing
    tcgplayer_market_price = Column(DECIMAL(10, 2))
    tcgplayer_low_price = Column(DECIMAL(10, 2))
    tcgplayer_mid_price = Column(DECIMAL(10, 2))
    tcgplayer_high_price = Column(DECIMAL(10, 2))
    tcgplayer_direct_low = Column(DECIMAL(10, 2))
    tcgplayer_last_updated = Column(DateTime(timezone=True))
    
    # eBay pricing
    ebay_avg_price = Column(DECIMAL(10, 2))
    ebay_quality_seller_avg = Column(DECIMAL(10, 2))
    ebay_auction_avg = Column(DECIMAL(10, 2))
    ebay_buy_it_now_avg = Column(DECIMAL(10, 2))
    ebay_sold_listings_30d = Column(Integer)
    ebay_last_updated = Column(DateTime(timezone=True))
    
    # Unified pricing intelligence
    market_price = Column(DECIMAL(10, 2))  # Our calculated market price
    confidence_score = Column(DECIMAL(3, 2))  # 0.00 to 1.00
    price_trend_7d = Column(DECIMAL(5, 2))  # Percentage change
    price_trend_30d = Column(DECIMAL(5, 2))  # Percentage change
    volatility_score = Column(DECIMAL(3, 2))  # Price volatility metric
    
    # Market metrics
    market_cap = Column(DECIMAL(15, 2))  # Estimated total market value
    liquidity_score = Column(DECIMAL(3, 2))  # How easy to buy/sell
    velocity_score = Column(DECIMAL(3, 2))  # Trading frequency
    
    # Regional pricing (optional)
    price_data_by_region = Column(JSON)
    
    # Data quality indicators
    data_sources = Column(JSON)  # Which sources contributed to pricing
    last_validation = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="pricing_data")
    
    # Indexes
    __table_args__ = (
        Index('idx_pricing_market_price', 'market_price'),
        Index('idx_pricing_updated', 'updated_at'),
    )


class PriceHistory(Base):
    """Historical pricing data for trend analysis"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Price data
    source = Column(String(20), nullable=False, index=True)  # tcgplayer, ebay, etc.
    price_type = Column(String(20), nullable=False)  # market, low, high, auction
    price = Column(DECIMAL(10, 2), nullable=False)
    condition = Column(String(10))  # NM, LP, MP, HP, DMG
    
    # Market context
    volume = Column(Integer)  # Number of sales/listings
    listings_count = Column(Integer)
    avg_condition = Column(String(10))
    
    # Metadata
    currency = Column(String(3), default="USD")
    region = Column(String(10))
    
    # Timestamp (partitioned for performance)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    date_only = Column(DateTime(timezone=True), index=True)  # For daily aggregations
    
    # Relationships
    product = relationship("Product", back_populates="price_history")
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_price_history_product_time', 'product_id', 'timestamp'),
        Index('idx_price_history_source_time', 'source', 'timestamp'),
        Index('idx_price_history_daily', 'product_id', 'date_only'),
    )


class ProductSet(Base):
    """Pokemon TCG set information"""
    __tablename__ = "product_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Set identification
    name = Column(String(255), nullable=False, unique=True, index=True)
    code = Column(String(20), unique=True, index=True)
    series = Column(String(100), index=True)
    
    # Set details
    release_date = Column(DateTime(timezone=True))
    total_cards = Column(Integer)
    legal_formats = Column(JSON)  # Standard, Expanded, etc.
    
    # Set metadata
    logo_url = Column(String(1000))
    symbol_url = Column(String(1000))
    description = Column(Text)
    
    # External IDs
    tcgplayer_group_id = Column(Integer, unique=True)
    pokemontcg_io_id = Column(String(50), unique=True)
    
    # Set statistics
    avg_card_price = Column(DECIMAL(10, 2))
    set_market_cap = Column(DECIMAL(15, 2))
    completion_cost = Column(DECIMAL(12, 2))  # Cost to complete set
    
    # Status
    is_active = Column(Boolean, default=True)
    is_standard_legal = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="set")


class ProductVariant(Base):
    """Product variants (different conditions, printings, etc.)"""
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    base_product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Variant specifications
    condition = Column(String(20), nullable=False)
    printing = Column(String(50))
    language = Column(String(10))
    grading = Column(String(20))  # PSA 10, BGS 9.5, etc.
    
    # Variant-specific pricing
    market_price = Column(DECIMAL(10, 2))
    tcgplayer_id = Column(Integer, unique=True)
    
    # Availability
    in_stock_count = Column(Integer, default=0)
    avg_shipping_time = Column(Integer)  # Days
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint on variant combination
    __table_args__ = (
        UniqueConstraint('base_product_id', 'condition', 'printing', 'language', 'grading'),
    )