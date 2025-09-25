"""
🎯 Set Collection API Schemas
Pydantic schemas for Pokemon TCG set collections matching pokedata.io structure
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal

from app.schemas.product_schemas import ProductSummary, PricingData


class SetSummary(BaseModel):
    """Basic set information for listings"""
    id: int = Field(..., description="Set ID")
    name: str = Field(..., description="Set name")
    code: Optional[str] = Field(None, description="Set code")
    series: Optional[str] = Field(None, description="Series name")
    symbol_url: Optional[str] = Field(None, description="Set symbol URL")
    logo_url: Optional[str] = Field(None, description="Set logo URL")
    release_date: Optional[datetime] = Field(None, description="Release date")
    total_cards: Optional[int] = Field(None, description="Total cards in set")
    
    # Market data
    avg_card_price: Optional[float] = Field(None, description="Average card price")
    set_market_cap: Optional[float] = Field(None, description="Total set market value")
    completion_cost: Optional[float] = Field(None, description="Cost to complete set")
    
    # Collection stats
    cards_owned: int = Field(default=0, description="Cards owned in collection")
    completion_percentage: float = Field(default=0.0, description="Collection completion %")
    
    class Config:
        from_attributes = True


class SetCard(BaseModel):
    """Card information within a set collection"""
    id: int = Field(..., description="Product ID")
    name: str = Field(..., description="Card name")
    number: Optional[str] = Field(None, description="Card number in set")
    rarity: Optional[str] = Field(None, description="Card rarity")
    image_url: Optional[str] = Field(None, description="Card image URL")
    
    # Pokemon-specific data
    hp: Optional[int] = Field(None, description="HP value")
    pokemon_type: Optional[str] = Field(None, description="Pokemon type")
    stage: Optional[str] = Field(None, description="Evolution stage")
    
    # Pricing information
    current_price: Optional[float] = Field(None, description="Current market price")
    price_trend: Optional[str] = Field(None, description="Price trend (up/down/stable)")
    pricing: Optional[PricingData] = Field(None, description="Detailed pricing data")
    
    # Collection status
    is_owned: bool = Field(default=False, description="Whether card is owned")
    condition: Optional[str] = Field(None, description="Card condition")
    purchase_price: Optional[float] = Field(None, description="Purchase price if owned")
    
    class Config:
        from_attributes = True


class SetCollection(BaseModel):
    """Complete set collection view matching pokedata.io"""
    # Set information
    id: int = Field(..., description="Set ID")
    name: str = Field(..., description="Set name")
    code: Optional[str] = Field(None, description="Set code")
    series: str = Field(..., description="Series name")
    symbol: Optional[str] = Field(None, description="Set symbol/code")
    
    # Set metadata
    release_date: Optional[datetime] = Field(None, description="Release date")
    description: Optional[str] = Field(None, description="Set description")
    logo_url: Optional[str] = Field(None, description="Set logo URL")
    symbol_url: Optional[str] = Field(None, description="Set symbol URL")
    
    # Collection statistics (matching pokedata.io layout)
    total_value: float = Field(..., description="Total collection value")
    completion_percentage: float = Field(..., description="Collection completion %")
    total_cards: int = Field(..., description="Total cards in set")
    cards_owned: int = Field(..., description="Cards owned")
    cards_missing: int = Field(..., description="Cards missing")
    secret_rares_owned: int = Field(default=0, description="Secret rares owned")
    secret_rares_total: int = Field(default=0, description="Total secret rares")
    
    # Card listing
    cards: List[SetCard] = Field(..., description="Cards in the set")
    
    class Config:
        from_attributes = True


class SetListResponse(BaseModel):
    """Paginated set list response"""
    items: List[SetSummary] = Field(..., description="List of sets")
    total: int = Field(..., description="Total number of sets")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Number of records returned")
    has_more: bool = Field(..., description="Whether more records are available")


class SetFilters(BaseModel):
    """Set collection filters"""
    search: Optional[str] = Field(None, description="Search term")
    series: Optional[str] = Field(None, description="Filter by series")
    format: Optional[str] = Field(None, description="Legal format (Standard, Expanded)")
    release_year: Optional[int] = Field(None, description="Release year")
    min_value: Optional[float] = Field(None, ge=0, description="Minimum set value")
    max_value: Optional[float] = Field(None, ge=0, description="Maximum set value")
    completion_status: Optional[str] = Field(None, description="complete/incomplete/not_started")
    is_standard_legal: Optional[bool] = Field(None, description="Standard legal sets only")


class UserSetProgress(BaseModel):
    """User's progress on a specific set"""
    set_id: int = Field(..., description="Set ID")
    user_id: int = Field(..., description="User ID")
    cards_owned: int = Field(..., description="Cards owned")
    total_invested: float = Field(..., description="Total amount invested")
    current_value: float = Field(..., description="Current collection value")
    profit_loss: float = Field(..., description="Profit/loss amount")
    profit_loss_percentage: float = Field(..., description="Profit/loss percentage")
    completion_percentage: float = Field(..., description="Collection completion %")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True