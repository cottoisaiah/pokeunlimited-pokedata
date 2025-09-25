"""
🎯 Product API Schemas
Pydantic schemas for product-related API endpoints
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal

# Base Schemas
class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., description="Product name")
    set_name: Optional[str] = Field(None, description="Pokemon set name")
    number: Optional[str] = Field(None, description="Card number")
    rarity: Optional[str] = Field(None, description="Card rarity")
    product_type: str = Field(default="Cards", description="Product type")
    description: Optional[str] = Field(None, description="Product description")
    image_url: Optional[str] = Field(None, description="Product image URL")

class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    tcgplayer_id: Optional[int] = Field(None, description="TCGPlayer product ID")
    tcgplayer_url: Optional[str] = Field(None, description="TCGPlayer product URL")
    is_tracked: bool = Field(default=True, description="Whether to track pricing")

class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, description="Product name")
    set_name: Optional[str] = Field(None, description="Pokemon set name") 
    number: Optional[str] = Field(None, description="Card number")
    rarity: Optional[str] = Field(None, description="Card rarity")
    description: Optional[str] = Field(None, description="Product description")
    image_url: Optional[str] = Field(None, description="Product image URL")
    is_tracked: Optional[bool] = Field(None, description="Whether to track pricing")
    is_active: Optional[bool] = Field(None, description="Whether product is active")

# Pricing Schemas
class PricingData(BaseModel):
    """Pricing information schema"""
    market_price: Optional[float] = Field(None, description="Current market price")
    tcgplayer_market_price: Optional[float] = Field(None, description="TCGPlayer market price")
    tcgplayer_low_price: Optional[float] = Field(None, description="TCGPlayer low price")
    tcgplayer_mid_price: Optional[float] = Field(None, description="TCGPlayer mid price")
    tcgplayer_high_price: Optional[float] = Field(None, description="TCGPlayer high price")
    ebay_average_price: Optional[float] = Field(None, description="eBay average price")
    ebay_low_price: Optional[float] = Field(None, description="eBay low price")
    ebay_high_price: Optional[float] = Field(None, description="eBay high price")
    confidence_score: Optional[float] = Field(None, description="Price confidence (0-1)")
    last_updated: Optional[datetime] = Field(None, description="Last price update")

class TCGPlayerPricing(BaseModel):
    """TCGPlayer specific pricing"""
    market_price: Optional[float] = Field(None, description="Market price")
    low_price: Optional[float] = Field(None, description="Low price")
    mid_price: Optional[float] = Field(None, description="Mid price")
    high_price: Optional[float] = Field(None, description="High price")
    direct_low_price: Optional[float] = Field(None, description="Direct low price")
    last_updated: Optional[datetime] = Field(None, description="Last updated")

class eBayPricing(BaseModel):
    """eBay specific pricing"""
    average_price: Optional[float] = Field(None, description="Average price")
    low_price: Optional[float] = Field(None, description="Low price")
    high_price: Optional[float] = Field(None, description="High price")
    listing_count: Optional[int] = Field(None, description="Number of active listings")
    last_updated: Optional[datetime] = Field(None, description="Last updated")

class ProductPricingData(BaseModel):
    """Comprehensive pricing data"""
    market_price: Optional[float] = Field(None, description="Unified market price")
    confidence_score: Optional[float] = Field(None, description="Price confidence (0-1)")
    tcgplayer: TCGPlayerPricing
    ebay: eBayPricing

class PriceHistoryPoint(BaseModel):
    """Single price history data point"""
    timestamp: datetime = Field(..., description="Price timestamp")
    price: float = Field(..., description="Price value")
    source: str = Field(..., description="Price source (tcgplayer, ebay)")
    price_type: str = Field(..., description="Price type (market, low, high)")

# Response Schemas
class ProductResponse(BaseModel):
    """Complete product response"""
    id: int = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    set_name: Optional[str] = Field(None, description="Pokemon set name")
    number: Optional[str] = Field(None, description="Card number")
    rarity: Optional[str] = Field(None, description="Card rarity")
    product_type: str = Field(..., description="Product type")
    description: Optional[str] = Field(None, description="Product description")
    image_url: Optional[str] = Field(None, description="Product image URL")
    tcgplayer_id: Optional[int] = Field(None, description="TCGPlayer product ID")
    tcgplayer_url: Optional[str] = Field(None, description="TCGPlayer product URL")
    is_tracked: bool = Field(..., description="Whether pricing is tracked")
    last_price_update: Optional[datetime] = Field(None, description="Last price update")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    pricing: Optional[PricingData] = Field(None, description="Current pricing data")
    price_history: Optional[List[PriceHistoryPoint]] = Field(None, description="Price history")

    class Config:
        from_attributes = True

class ProductSummary(BaseModel):
    """Summary product information for lists"""
    id: int = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    set_name: Optional[str] = Field(None, description="Pokemon set name")
    number: Optional[str] = Field(None, description="Card number")
    rarity: Optional[str] = Field(None, description="Card rarity")
    product_type: str = Field(..., description="Product type")
    image_url: Optional[str] = Field(None, description="Product image URL")
    is_tracked: bool = Field(..., description="Whether pricing is tracked")
    last_price_update: Optional[datetime] = Field(None, description="Last price update")
    created_at: datetime = Field(..., description="Creation timestamp")
    pricing: Optional[PricingData] = Field(None, description="Current pricing data")

    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    """Paginated product list response"""
    items: List[ProductSummary] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Number of records returned")
    has_more: bool = Field(..., description="Whether more records are available")

class ProductPricingResponse(BaseModel):
    """Product pricing response"""
    product_id: int = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    last_updated: Optional[datetime] = Field(None, description="Last price update")
    pricing_data: ProductPricingData = Field(..., description="Comprehensive pricing data")

class PriceHistoryResponse(BaseModel):
    """Price history response"""
    product_id: int = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    period_days: int = Field(..., description="Number of days of history")
    data_points: int = Field(..., description="Total number of data points")
    sources: Dict[str, List[PriceHistoryPoint]] = Field(..., description="Price data by source")

# Search and Filter Schemas
class ProductSearchFilters(BaseModel):
    """Product search filters"""
    search: Optional[str] = Field(None, description="Search term")
    set_name: Optional[str] = Field(None, description="Filter by set name")
    rarity: Optional[str] = Field(None, description="Filter by rarity")
    product_type: Optional[str] = Field(None, description="Filter by product type")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    is_tracked: Optional[bool] = Field(None, description="Filter by tracking status")
    has_pricing: Optional[bool] = Field(None, description="Filter products with pricing data")
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than or equal to min_price')
        return v

class ProductSort(BaseModel):
    """Product sorting options"""
    sort_by: str = Field(default="name", description="Field to sort by")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")

# Set Information Schemas
class SetInfo(BaseModel):
    """Pokemon set information"""
    name: str = Field(..., description="Set name")
    product_count: int = Field(..., description="Number of products in set")
    first_added: Optional[datetime] = Field(None, description="When first product was added")
    last_updated: Optional[datetime] = Field(None, description="Last price update in set")

# Market Insights Schemas
class MarketTrendData(BaseModel):
    """Market trend information"""
    trend_direction: str = Field(..., description="Price trend direction")
    trend_strength: float = Field(..., description="Trend strength (0-1)")
    price_change_percentage: float = Field(..., description="Price change percentage")

class MarketInsights(BaseModel):
    """Comprehensive market insights"""
    product_id: int = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    set_name: Optional[str] = Field(None, description="Set name")
    insights: Dict[str, Any] = Field(..., description="Market insights data")
    generated_at: datetime = Field(..., description="When insights were generated")

# Validation Schemas
class ProductValidation(BaseModel):
    """Product validation response"""
    is_valid: bool = Field(..., description="Whether product data is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")

# Bulk Operation Schemas
class BulkProductCreate(BaseModel):
    """Bulk product creation"""
    products: List[ProductCreate] = Field(..., description="List of products to create")
    skip_duplicates: bool = Field(default=True, description="Skip duplicate products")

class BulkProductResponse(BaseModel):
    """Bulk operation response"""
    created_count: int = Field(..., description="Number of products created")
    skipped_count: int = Field(..., description="Number of products skipped")
    error_count: int = Field(..., description="Number of products with errors")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Creation errors")

# Statistics Schemas
class ProductStats(BaseModel):
    """Product catalog statistics"""
    total_products: int = Field(..., description="Total number of products")
    tracked_products: int = Field(..., description="Number of tracked products")
    sets_count: int = Field(..., description="Number of unique sets")
    avg_price: Optional[float] = Field(None, description="Average product price")
    price_coverage: float = Field(..., description="Percentage of products with pricing")
    last_sync: Optional[datetime] = Field(None, description="Last catalog sync")

# TCGPlayer Integration Schemas
class TCGPlayerSync(BaseModel):
    """TCGPlayer sync configuration"""
    max_products: int = Field(default=1000, ge=1, le=10000, description="Maximum products to sync")
    update_existing: bool = Field(default=False, description="Update existing products")
    categories: List[str] = Field(default_factory=lambda: ["Pokemon"], description="Categories to sync")

class TCGPlayerSyncResponse(BaseModel):
    """TCGPlayer sync response"""
    synced_count: int = Field(..., description="Number of products synced")
    updated_count: int = Field(..., description="Number of products updated")
    error_count: int = Field(..., description="Number of sync errors")
    duration_seconds: float = Field(..., description="Sync duration in seconds")
    errors: List[str] = Field(default_factory=list, description="Sync errors")