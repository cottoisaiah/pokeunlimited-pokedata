"""
🎯 PokeData Cards Models
TCGdex card data with eBay pricing integration
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, Text,
    DECIMAL, JSON, Index, UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.database import Base


class PokeDataCard(Base):
    """TCGdex card data with eBay pricing integration"""
    __tablename__ = "pokedata_cards"

    id = Column(Integer, primary_key=True, index=True)

    # TCGdex card identifiers
    tcgdex_id = Column(String(50), index=True, nullable=False)  # e.g., "base1-1"
    local_id = Column(String(20), nullable=False)  # Card number in set
    name = Column(String(500), nullable=False, index=True)

    # Language support
    language = Column(String(10), default="en", index=True)  # en, ja, zh, ko

    # Set information
    set_id = Column(String(20), nullable=False, index=True)  # TCGdex set ID
    pokedata_set_id = Column(Integer, ForeignKey('pokedata_sets.id'), nullable=True)  # Foreign key to PokeDataSet
    set_name = Column(String(255), index=True)
    set_code = Column(String(20))
    set_release_date = Column(DateTime(timezone=True))
    set_total_cards = Column(Integer)

    # Card classification
    category = Column(String(50), index=True)  # Pokemon, Trainer, Energy
    rarity = Column(String(50), index=True)
    illustrator = Column(String(255))

    # Pokemon-specific attributes
    hp = Column(Integer)
    types = Column(JSON)  # List of types ["Fire", "Water", etc.]
    stage = Column(String(50))  # Basic, Stage 1, Stage 2, etc.
    evolves_from = Column(String(255))
    abilities = Column(JSON)  # List of abilities
    attacks = Column(JSON)  # List of attacks
    weaknesses = Column(JSON)  # List of weaknesses
    resistances = Column(JSON)  # List of resistances
    retreat_cost = Column(Integer)

    # Visual information
    image_url = Column(String(1000))
    image_urls = Column(JSON)  # Multiple image URLs for different qualities

    # Card variants
    variants = Column(JSON)  # normal, reverse, holo, firstEdition, etc.

    # Legal information
    legal = Column(JSON)  # Standard, Expanded legality

    # External IDs for cross-referencing
    tcgplayer_id = Column(String(50), index=True)
    ebay_product_id = Column(String(50), index=True)

    # eBay pricing data
    ebay_avg_price = Column(DECIMAL(10, 2))
    ebay_median_price = Column(DECIMAL(10, 2))
    ebay_low_price = Column(DECIMAL(10, 2))
    ebay_high_price = Column(DECIMAL(10, 2))
    ebay_sold_count_30d = Column(Integer, default=0)
    ebay_active_listings = Column(Integer, default=0)
    ebay_price_confidence = Column(DECIMAL(3, 2))  # 0.00 to 1.00

    # Market intelligence
    market_price = Column(DECIMAL(10, 2))  # Calculated market price
    price_trend_7d = Column(DECIMAL(5, 2))  # Percentage change
    price_trend_30d = Column(DECIMAL(5, 2))  # Percentage change
    volatility_score = Column(DECIMAL(3, 2))  # Price volatility
    liquidity_score = Column(DECIMAL(3, 2))  # Trading liquidity

    # Status and tracking
    is_active = Column(Boolean, default=True)
    is_priced = Column(Boolean, default=False)  # Whether we have pricing data
    last_ebay_update = Column(DateTime(timezone=True))
    last_tcgdex_update = Column(DateTime(timezone=True))

    # Raw data storage for future processing
    raw_tcgdex_data = Column(JSON)
    raw_ebay_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_pokedata_card_tcgdex_id_lang', 'tcgdex_id', 'language'),
        Index('idx_pokedata_card_set_lang', 'set_id', 'language'),
        Index('idx_pokedata_card_category_rarity', 'category', 'rarity'),
        Index('idx_pokedata_card_name_lang', 'name', 'language'),
        UniqueConstraint('tcgdex_id', 'language', name='uq_pokedata_card_tcgdex_id_lang'),
    )

    def __repr__(self):
        return f"<PokeDataCard(id={self.id}, name='{self.name}', set='{self.set_name}', lang='{self.language}')>"


class PokeDataSet(Base):
    """TCGdex set data for reference"""
    __tablename__ = "pokedata_sets"

    id = Column(Integer, primary_key=True, index=True)

    # TCGdex set identifiers
    tcgdex_id = Column(String(20), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(20))

    # Language support
    language = Column(String(10), default="en", index=True)

    # Set information
    release_date = Column(DateTime(timezone=True))
    total_cards = Column(Integer)
    legal = Column(JSON)  # Standard, Expanded legality

    # Visual information
    logo_url = Column(String(1000))
    symbol_url = Column(String(1000))

    # Set metadata
    serie_name = Column(String(255))
    serie_code = Column(String(20))

    # Status
    is_active = Column(Boolean, default=True)

    # Raw data storage
    raw_tcgdex_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cards = relationship("PokeDataCard", backref="pokedata_set", foreign_keys="PokeDataCard.pokedata_set_id")

    # Indexes
    __table_args__ = (
        Index('idx_pokedata_set_tcgdex_id_lang', 'tcgdex_id', 'language'),
        UniqueConstraint('tcgdex_id', 'language', name='uq_pokedata_set_tcgdex_id_lang'),
    )

    def __repr__(self):
        return f"<PokeDataSet(id={self.id}, name='{self.name}', code='{self.code}', lang='{self.language}')>"