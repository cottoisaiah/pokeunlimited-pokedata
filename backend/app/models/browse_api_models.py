"""
Enhanced models for Browse API integration
"""

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
import json

from app.models.database import Base

class EbayApiUsage(Base):
    """Track eBay API usage for rate limiting"""
    __tablename__ = 'ebay_api_usage'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    api_type = Column(String(50), nullable=False)  # 'browse', 'trading', etc.
    calls_made = Column(Integer, default=0)
    calls_limit = Column(Integer, default=5000)
    rate_limit_hits = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'api_type': self.api_type,
            'calls_made': self.calls_made,
            'calls_limit': self.calls_limit,
            'usage_percentage': round((self.calls_made / self.calls_limit * 100), 2) if self.calls_limit > 0 else 0,
            'rate_limit_hits': self.rate_limit_hits,
            'errors_count': self.errors_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MarketTrend(Base):
    """Market trend analysis for cards"""
    __tablename__ = 'browse_market_trends'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    trend_date = Column(Date, nullable=False)
    trend_direction = Column(String(20), nullable=False)  # 'up', 'down', 'stable'
    price_change_pct = Column(Numeric(8, 4), nullable=True)
    volume_change_pct = Column(Numeric(8, 4), nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    trend_strength = Column(String(20), nullable=True)  # 'weak', 'moderate', 'strong'
    supporting_indicators = Column(Text, nullable=True)  # JSON data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship - temporarily disabled for initial deployment
    # monitored_card = relationship("MonitoredCard", back_populates="trends")
    
    def get_supporting_indicators(self):
        """Parse supporting indicators JSON"""
        if self.supporting_indicators:
            try:
                return json.loads(self.supporting_indicators)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_supporting_indicators(self, indicators_dict):
        """Set supporting indicators as JSON"""
        self.supporting_indicators = json.dumps(indicators_dict) if indicators_dict else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'monitored_card_id': self.monitored_card_id,
            'trend_date': self.trend_date.isoformat() if self.trend_date else None,
            'trend_direction': self.trend_direction,
            'price_change_pct': float(self.price_change_pct) if self.price_change_pct else None,
            'volume_change_pct': float(self.volume_change_pct) if self.volume_change_pct else None,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'trend_strength': self.trend_strength,
            'supporting_indicators': self.get_supporting_indicators(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CompetitorAnalysis(Base):
    """Competitor analysis data"""
    __tablename__ = 'competitor_analysis'
    
    id = Column(Integer, primary_key=True)
    competitor_name = Column(String(100), nullable=False)
    ebay_store_name = Column(String(100), nullable=True)
    analysis_date = Column(Date, nullable=False)
    total_listings = Column(Integer, default=0)
    avg_price = Column(Numeric(10, 2), nullable=True)
    price_range_low = Column(Numeric(10, 2), nullable=True)
    price_range_high = Column(Numeric(10, 2), nullable=True)
    listing_types = Column(Text, nullable=True)  # JSON data
    categories_active = Column(Text, nullable=True)  # JSON data
    seller_rating = Column(Numeric(5, 2), nullable=True)
    market_share_estimate = Column(Numeric(5, 2), nullable=True)
    competitive_advantage = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def get_listing_types(self):
        """Parse listing types JSON"""
        if self.listing_types:
            try:
                return json.loads(self.listing_types)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_listing_types(self, types_dict):
        """Set listing types as JSON"""
        self.listing_types = json.dumps(types_dict) if types_dict else None
    
    def get_categories_active(self):
        """Parse active categories JSON"""
        if self.categories_active:
            try:
                return json.loads(self.categories_active)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_categories_active(self, categories_list):
        """Set active categories as JSON"""
        self.categories_active = json.dumps(categories_list) if categories_list else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'competitor_name': self.competitor_name,
            'ebay_store_name': self.ebay_store_name,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'total_listings': self.total_listings,
            'avg_price': float(self.avg_price) if self.avg_price else None,
            'price_range_low': float(self.price_range_low) if self.price_range_low else None,
            'price_range_high': float(self.price_range_high) if self.price_range_high else None,
            'listing_types': self.get_listing_types(),
            'categories_active': self.get_categories_active(),
            'seller_rating': float(self.seller_rating) if self.seller_rating else None,
            'market_share_estimate': float(self.market_share_estimate) if self.market_share_estimate else None,
            'competitive_advantage': self.competitive_advantage,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PriceAlert(Base):
    """Price alert configuration for browse API"""
    __tablename__ = 'browse_price_alerts'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # 'price_drop', 'price_spike', 'volume_change'
    threshold_value = Column(Numeric(10, 2), nullable=False)
    threshold_type = Column(String(20), nullable=False)  # 'absolute', 'percentage'
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    notification_email = Column(String(255), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship - temporarily disabled for initial deployment
    # monitored_card = relationship("MonitoredCard", back_populates="price_alerts")
    
    def to_dict(self):
        return {
            'id': self.id,
            'monitored_card_id': self.monitored_card_id,
            'alert_type': self.alert_type,
            'threshold_value': float(self.threshold_value),
            'threshold_type': self.threshold_type,
            'is_active': self.is_active,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'trigger_count': self.trigger_count,
            'notification_email': self.notification_email,
            'webhook_url': self.webhook_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Enhanced EbayListingData model (extends existing)
class EnhancedEbayListingData:
    """Enhanced fields for eBay Browse API data"""
    
    # New fields to add to existing EbayListingData model
    item_web_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    buy_it_now_available = Column(Boolean, default=True)
    auction_format = Column(Boolean, default=False)
    shipping_cost = Column(Numeric(10, 2), nullable=True)
    seller_feedback_percentage = Column(Numeric(5, 2), nullable=True)
    category_name = Column(String(200), nullable=True)
    watchers_count = Column(Integer, default=0)
    currency_code = Column(String(3), default='USD')
    
    def enhanced_to_dict(self):
        """Enhanced dictionary representation including new fields"""
        base_dict = self.to_dict() if hasattr(self, 'to_dict') else {}
        
        enhanced_fields = {
            'item_web_url': self.item_web_url,
            'image_url': self.image_url,
            'buy_it_now_available': self.buy_it_now_available,
            'auction_format': self.auction_format,
            'shipping_cost': float(self.shipping_cost) if self.shipping_cost else None,
            'seller_feedback_percentage': float(self.seller_feedback_percentage) if self.seller_feedback_percentage else None,
            'category_name': self.category_name,
            'watchers_count': self.watchers_count,
            'currency_code': self.currency_code
        }
        
        return {**base_dict, **enhanced_fields}

# Enhanced DataCollectionLog model (extends existing)
class EnhancedDataCollectionLog:
    """Enhanced fields for data collection tracking"""
    
    # New fields to add to existing DataCollectionLog model
    api_calls_made = Column(Integer, default=0)
    rate_limit_hits = Column(Integer, default=0)
    data_source = Column(String(50), default='ebay_browse')
    collection_scope = Column(String(100), nullable=True)  # e.g., 'full', 'incremental', 'category_123'
    
    def enhanced_to_dict(self):
        """Enhanced dictionary representation including new fields"""
        base_dict = self.to_dict() if hasattr(self, 'to_dict') else {}
        
        enhanced_fields = {
            'api_calls_made': self.api_calls_made,
            'rate_limit_hits': self.rate_limit_hits,
            'data_source': self.data_source,
            'collection_scope': self.collection_scope
        }
        
        return {**base_dict, **enhanced_fields}

# Market Intelligence Service enhancements
class MarketIntelligenceAnalytics:
    """Helper class for market intelligence analytics"""
    
    @staticmethod
    def calculate_trend_strength(price_change_pct, volume_change_pct):
        """Calculate trend strength based on price and volume changes"""
        if not price_change_pct:
            return 'unknown'
        
        abs_price_change = abs(price_change_pct)
        abs_volume_change = abs(volume_change_pct) if volume_change_pct else 0
        
        # Strong trend: >10% price change OR >20% volume change
        if abs_price_change > 10 or abs_volume_change > 20:
            return 'strong'
        # Moderate trend: 5-10% price change OR 10-20% volume change
        elif abs_price_change > 5 or abs_volume_change > 10:
            return 'moderate'
        # Weak trend: <5% price change AND <10% volume change
        else:
            return 'weak'
    
    @staticmethod
    def calculate_confidence_score(data_points, time_range_days, volatility):
        """Calculate confidence score for trend analysis"""
        base_score = 0.5  # Base confidence
        
        # More data points increase confidence
        data_factor = min(data_points / 50, 0.3)  # Max 0.3 boost for 50+ data points
        
        # Longer time range increases confidence
        time_factor = min(time_range_days / 30, 0.2)  # Max 0.2 boost for 30+ days
        
        # Lower volatility increases confidence
        volatility_factor = max(0, 0.2 - (volatility / 100))  # Penalize high volatility
        
        confidence = base_score + data_factor + time_factor + volatility_factor
        return min(confidence, 1.0)  # Cap at 1.0
    
    @staticmethod
    def get_trend_direction(price_change_pct, threshold=2.0):
        """Determine trend direction based on price change"""
        if not price_change_pct:
            return 'stable'
        
        if price_change_pct > threshold:
            return 'up'
        elif price_change_pct < -threshold:
            return 'down'
        else:
            return 'stable'
