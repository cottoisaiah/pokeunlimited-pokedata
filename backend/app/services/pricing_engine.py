"""
🎯 Pricing Intelligence Engine
Advanced ML-powered pricing analysis and market intelligence
"""

import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import structlog
import numpy as np
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.database import get_db_session
from app.models.product_models import Product, ProductPricing, PriceHistory
from app.models.analytics_models import MarketTrend, PriceAlert
from app.services.cache_service import cache_service
from app.services.tcgplayer_service import tcgplayer_service
from app.services.ebay_service import ebay_service

logger = structlog.get_logger(__name__)

class TrendDirection(Enum):
    """Price trend directions"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"

class MarketSentiment(Enum):
    """Market sentiment indicators"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"

@dataclass
class PricePoint:
    """Individual price data point"""
    price: float
    timestamp: datetime
    source: str
    confidence: float

@dataclass
class PricingAnalysis:
    """Comprehensive pricing analysis result"""
    product_id: int
    product_name: str
    current_price: Optional[float]
    price_confidence: float
    
    # Trend analysis
    trend_direction: TrendDirection
    trend_strength: float
    price_velocity: float  # Rate of change
    
    # Market sentiment
    market_sentiment: MarketSentiment
    sentiment_score: float
    
    # Statistical analysis
    price_volatility: float
    support_level: Optional[float]
    resistance_level: Optional[float]
    
    # Data sources
    tcgplayer_data: Optional[Dict[str, Any]]
    ebay_data: Optional[Dict[str, Any]]
    
    # Recommendations
    buy_recommendation: str
    sell_recommendation: str
    target_price: Optional[float]
    
    # Metadata
    analysis_timestamp: datetime
    data_points_count: int

@dataclass
class MarketOverview:
    """Market-wide analysis overview"""
    total_products: int
    trending_up: int
    trending_down: int
    stable_products: int
    volatile_products: int
    
    average_volatility: float
    market_sentiment: MarketSentiment
    hot_products: List[Dict[str, Any]]
    declining_products: List[Dict[str, Any]]
    
    timestamp: datetime

class PricingIntelligenceEngine:
    """Advanced pricing intelligence and market analysis engine"""
    
    def __init__(self):
        self.min_data_points = 3
        self.volatility_threshold = 0.15  # 15%
        self.trend_threshold = 0.05  # 5%
        self.confidence_weights = {
            "tcgplayer": 0.6,
            "ebay": 0.4
        }
    
    async def analyze_product_pricing(
        self,
        product_id: int,
        days_back: int = 30
    ) -> Optional[PricingAnalysis]:
        """Comprehensive pricing analysis for a single product"""
        logger.info(f"Starting pricing analysis for product {product_id}")
        
        try:
            async with get_db_session() as db:
                # Get product with pricing data
                query = (
                    select(Product)
                    .options(selectinload(Product.pricing))
                    .where(Product.id == product_id)
                )
                result = await db.execute(query)
                product = result.scalar_one_or_none()
                
                if not product:
                    logger.warning(f"Product {product_id} not found")
                    return None
                
                # Get price history
                history_query = (
                    select(PriceHistory)
                    .where(
                        PriceHistory.product_id == product_id,
                        PriceHistory.timestamp >= datetime.utcnow() - timedelta(days=days_back)
                    )
                    .order_by(PriceHistory.timestamp.asc())
                )
                history_result = await db.execute(history_query)
                price_history = history_result.scalars().all()
                
                # Convert to price points
                price_points = [
                    PricePoint(
                        price=h.price,
                        timestamp=h.timestamp,
                        source=h.source,
                        confidence=self.confidence_weights.get(h.source, 0.5)
                    )
                    for h in price_history
                    if h.price > 0
                ]
                
                if len(price_points) < self.min_data_points:
                    logger.warning(f"Insufficient price data for product {product_id}")
                    return None
                
                # Perform analysis
                analysis = await self._perform_comprehensive_analysis(
                    product, price_points
                )
                
                # Cache the result
                cache_key = f"pricing_analysis:{product_id}:{days_back}"
                await cache_service.set(
                    cache_key,
                    asdict(analysis),
                    ttl=settings.CACHE_TTL_ANALYTICS,
                    prefix="analytics"
                )
                
                return analysis
                
        except Exception as e:
            logger.error(f"Pricing analysis failed for product {product_id}: {e}")
            return None
    
    async def _perform_comprehensive_analysis(
        self,
        product: Product,
        price_points: List[PricePoint]
    ) -> PricingAnalysis:
        """Perform comprehensive pricing analysis"""
        
        # Basic statistics
        prices = [p.price for p in price_points]
        current_price = prices[-1] if prices else None
        
        # Calculate weighted current price based on source confidence
        if len(price_points) > 1:
            recent_points = price_points[-5:]  # Last 5 data points
            total_weight = sum(p.confidence for p in recent_points)
            if total_weight > 0:
                current_price = sum(
                    p.price * p.confidence for p in recent_points
                ) / total_weight
        
        # Trend analysis
        trend_direction, trend_strength, price_velocity = self._analyze_trend(price_points)
        
        # Volatility analysis
        price_volatility = self._calculate_volatility(prices)
        
        # Support and resistance levels
        support_level, resistance_level = self._calculate_support_resistance(prices)
        
        # Market sentiment analysis
        market_sentiment, sentiment_score = self._analyze_market_sentiment(
            price_points, trend_direction, price_volatility
        )
        
        # Price confidence score
        price_confidence = self._calculate_price_confidence(price_points)
        
        # External data integration
        tcgplayer_data = await self._get_tcgplayer_insights(product)
        ebay_data = await self._get_ebay_insights(product)
        
        # Generate recommendations
        buy_rec, sell_rec, target_price = self._generate_recommendations(
            current_price, trend_direction, market_sentiment, price_volatility
        )
        
        return PricingAnalysis(
            product_id=product.id,
            product_name=product.name,
            current_price=current_price,
            price_confidence=price_confidence,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            price_velocity=price_velocity,
            market_sentiment=market_sentiment,
            sentiment_score=sentiment_score,
            price_volatility=price_volatility,
            support_level=support_level,
            resistance_level=resistance_level,
            tcgplayer_data=tcgplayer_data,
            ebay_data=ebay_data,
            buy_recommendation=buy_rec,
            sell_recommendation=sell_rec,
            target_price=target_price,
            analysis_timestamp=datetime.utcnow(),
            data_points_count=len(price_points)
        )
    
    def _analyze_trend(
        self, price_points: List[PricePoint]
    ) -> Tuple[TrendDirection, float, float]:
        """Analyze price trend using multiple methods"""
        if len(price_points) < 3:
            return TrendDirection.STABLE, 0.0, 0.0
        
        prices = [p.price for p in price_points]
        timestamps = [p.timestamp for p in price_points]
        
        # Calculate simple moving averages
        if len(prices) >= 7:
            short_ma = sum(prices[-7:]) / 7
            long_ma = sum(prices) / len(prices)
            ma_signal = (short_ma - long_ma) / long_ma
        else:
            ma_signal = 0
        
        # Linear regression for trend
        x_values = [(t - timestamps[0]).total_seconds() for t in timestamps]
        n = len(prices)
        
        # Calculate slope (price velocity)
        x_mean = sum(x_values) / n
        y_mean = sum(prices) / n
        
        numerator = sum((x_values[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Price velocity (percentage change per day)
        time_span_days = (timestamps[-1] - timestamps[0]).total_seconds() / 86400
        if time_span_days > 0 and y_mean > 0:
            price_velocity = (slope * 86400) / y_mean  # Daily percentage change
        else:
            price_velocity = 0
        
        # Recent price momentum
        if len(prices) >= 3:
            recent_change = (prices[-1] - prices[-3]) / prices[-3]
        else:
            recent_change = 0
        
        # Combine signals
        trend_signal = (ma_signal + recent_change) / 2
        trend_strength = abs(trend_signal)
        
        # Determine trend direction
        if abs(trend_signal) < self.trend_threshold:
            direction = TrendDirection.STABLE
        elif trend_signal > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        # Check for volatility
        volatility = self._calculate_volatility(prices)
        if volatility > self.volatility_threshold * 2:
            direction = TrendDirection.VOLATILE
        
        return direction, trend_strength, price_velocity
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility (coefficient of variation)"""
        if len(prices) < 2:
            return 0.0
        
        mean_price = statistics.mean(prices)
        if mean_price == 0:
            return 0.0
        
        variance = statistics.variance(prices)
        std_dev = variance ** 0.5
        
        return std_dev / mean_price
    
    def _calculate_support_resistance(
        self, prices: List[float]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculate support and resistance levels"""
        if len(prices) < 5:
            return None, None
        
        # Sort prices to find levels
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        
        # Support level (around 20th percentile)
        support_idx = max(0, int(n * 0.2))
        support_level = sorted_prices[support_idx]
        
        # Resistance level (around 80th percentile)
        resistance_idx = min(n - 1, int(n * 0.8))
        resistance_level = sorted_prices[resistance_idx]
        
        return support_level, resistance_level
    
    def _analyze_market_sentiment(
        self,
        price_points: List[PricePoint],
        trend_direction: TrendDirection,
        volatility: float
    ) -> Tuple[MarketSentiment, float]:
        """Analyze market sentiment based on multiple factors"""
        
        # Base sentiment from trend
        if trend_direction == TrendDirection.INCREASING:
            base_sentiment = 0.6
        elif trend_direction == TrendDirection.DECREASING:
            base_sentiment = -0.6
        elif trend_direction == TrendDirection.VOLATILE:
            base_sentiment = 0.0
        else:  # STABLE
            base_sentiment = 0.1
        
        # Adjust for volatility
        volatility_adjustment = min(volatility * 2, 0.4)
        if volatility > self.volatility_threshold:
            base_sentiment -= volatility_adjustment
        
        # Volume sentiment (more data points = higher confidence)
        volume_factor = min(len(price_points) / 20, 1.0)
        sentiment_score = base_sentiment * volume_factor
        
        # Determine sentiment category
        if sentiment_score > 0.3:
            sentiment = MarketSentiment.BULLISH
        elif sentiment_score < -0.3:
            sentiment = MarketSentiment.BEARISH
        elif abs(sentiment_score) < 0.1:
            sentiment = MarketSentiment.NEUTRAL
        else:
            sentiment = MarketSentiment.UNCERTAIN
        
        return sentiment, sentiment_score
    
    def _calculate_price_confidence(self, price_points: List[PricePoint]) -> float:
        """Calculate confidence in current price estimate"""
        if not price_points:
            return 0.0
        
        # Base confidence from data quantity
        data_confidence = min(len(price_points) / 10, 1.0)
        
        # Source diversity confidence
        sources = set(p.source for p in price_points)
        source_confidence = min(len(sources) / 3, 1.0)
        
        # Recency confidence (recent data is more valuable)
        now = datetime.utcnow()
        recent_points = [
            p for p in price_points
            if (now - p.timestamp).total_seconds() < 86400 * 7  # Last 7 days
        ]
        recency_confidence = min(len(recent_points) / 5, 1.0)
        
        # Weighted average confidence from sources
        total_weight = sum(p.confidence for p in price_points)
        if total_weight > 0:
            source_weight_confidence = total_weight / len(price_points)
        else:
            source_weight_confidence = 0.5
        
        # Combine factors
        overall_confidence = (
            data_confidence * 0.3 +
            source_confidence * 0.2 +
            recency_confidence * 0.3 +
            source_weight_confidence * 0.2
        )
        
        return min(overall_confidence, 1.0)
    
    async def _get_tcgplayer_insights(self, product: Product) -> Optional[Dict[str, Any]]:
        """Get additional insights from TCGPlayer"""
        if not product.tcgplayer_id:
            return None
        
        try:
            # Get detailed product info
            details = await tcgplayer_service.get_product_details(product.tcgplayer_id)
            if not details:
                return None
            
            # Get current pricing
            pricing_data = await tcgplayer_service.get_product_pricing([product.tcgplayer_id])
            pricing = pricing_data[0] if pricing_data else None
            
            return {
                "product_details": details,
                "current_pricing": {
                    "market_price": pricing.market_price if pricing else None,
                    "low_price": pricing.low_price if pricing else None,
                    "high_price": pricing.high_price if pricing else None,
                    "direct_low_price": pricing.direct_low_price if pricing else None
                } if pricing else None,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Failed to get TCGPlayer insights for product {product.id}: {e}")
            return None
    
    async def _get_ebay_insights(self, product: Product) -> Optional[Dict[str, Any]]:
        """Get additional insights from eBay"""
        try:
            # Build search query
            search_query = product.name
            if product.set_name:
                search_query += f" {product.set_name}"
            
            # Get market insights
            insights = await ebay_service.get_market_insights(
                product.name, product.set_name
            )
            
            return insights
            
        except Exception as e:
            logger.warning(f"Failed to get eBay insights for product {product.id}: {e}")
            return None
    
    def _generate_recommendations(
        self,
        current_price: Optional[float],
        trend_direction: TrendDirection,
        market_sentiment: MarketSentiment,
        volatility: float
    ) -> Tuple[str, str, Optional[float]]:
        """Generate buy/sell recommendations and target price"""
        
        if not current_price:
            return "HOLD", "HOLD", None
        
        # Buy recommendation logic
        if (trend_direction == TrendDirection.INCREASING and 
            market_sentiment in [MarketSentiment.BULLISH, MarketSentiment.NEUTRAL] and
            volatility < self.volatility_threshold):
            buy_rec = "STRONG_BUY"
            target_multiplier = 1.15
        elif (trend_direction == TrendDirection.STABLE and
              market_sentiment == MarketSentiment.BULLISH):
            buy_rec = "BUY"
            target_multiplier = 1.10
        elif volatility > self.volatility_threshold * 1.5:
            buy_rec = "WAIT"
            target_multiplier = 0.95
        else:
            buy_rec = "HOLD"
            target_multiplier = 1.05
        
        # Sell recommendation logic
        if (trend_direction == TrendDirection.DECREASING and
            market_sentiment in [MarketSentiment.BEARISH, MarketSentiment.UNCERTAIN]):
            sell_rec = "STRONG_SELL"
        elif (trend_direction == TrendDirection.VOLATILE or
              volatility > self.volatility_threshold * 2):
            sell_rec = "CONSIDER_SELL"
        elif (trend_direction == TrendDirection.INCREASING and
              market_sentiment == MarketSentiment.BULLISH):
            sell_rec = "HOLD_FOR_GAINS"
        else:
            sell_rec = "HOLD"
        
        # Calculate target price
        target_price = current_price * target_multiplier
        
        return buy_rec, sell_rec, target_price
    
    async def generate_market_overview(self, limit: int = 100) -> MarketOverview:
        """Generate comprehensive market overview"""
        logger.info("Generating market overview")
        
        try:
            async with get_db_session() as db:
                # Get top tracked products
                query = (
                    select(Product)
                    .where(Product.is_tracked == True)
                    .order_by(Product.last_price_update.desc())
                    .limit(limit)
                )
                result = await db.execute(query)
                products = result.scalars().all()
                
                # Analyze each product
                trend_counts = {
                    TrendDirection.INCREASING: 0,
                    TrendDirection.DECREASING: 0,
                    TrendDirection.STABLE: 0,
                    TrendDirection.VOLATILE: 0
                }
                
                volatilities = []
                hot_products = []
                declining_products = []
                sentiment_scores = []
                
                for product in products:
                    try:
                        analysis = await self.analyze_product_pricing(product.id, days_back=7)
                        if not analysis:
                            continue
                        
                        # Count trends
                        trend_counts[analysis.trend_direction] += 1
                        
                        # Collect volatilities
                        volatilities.append(analysis.price_volatility)
                        
                        # Collect sentiment scores
                        sentiment_scores.append(analysis.sentiment_score)
                        
                        # Identify hot products (strong upward trend)
                        if (analysis.trend_direction == TrendDirection.INCREASING and
                            analysis.trend_strength > 0.1):
                            hot_products.append({
                                "id": product.id,
                                "name": product.name,
                                "current_price": analysis.current_price,
                                "trend_strength": analysis.trend_strength,
                                "price_velocity": analysis.price_velocity
                            })
                        
                        # Identify declining products
                        if (analysis.trend_direction == TrendDirection.DECREASING and
                            analysis.trend_strength > 0.1):
                            declining_products.append({
                                "id": product.id,
                                "name": product.name,
                                "current_price": analysis.current_price,
                                "trend_strength": analysis.trend_strength,
                                "price_velocity": analysis.price_velocity
                            })
                            
                    except Exception as e:
                        logger.warning(f"Failed to analyze product {product.id}: {e}")
                        continue
                
                # Calculate market sentiment
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                    if avg_sentiment > 0.2:
                        market_sentiment = MarketSentiment.BULLISH
                    elif avg_sentiment < -0.2:
                        market_sentiment = MarketSentiment.BEARISH
                    else:
                        market_sentiment = MarketSentiment.NEUTRAL
                else:
                    market_sentiment = MarketSentiment.NEUTRAL
                
                # Sort hot and declining products
                hot_products.sort(key=lambda x: x["trend_strength"], reverse=True)
                declining_products.sort(key=lambda x: x["trend_strength"], reverse=True)
                
                return MarketOverview(
                    total_products=len(products),
                    trending_up=trend_counts[TrendDirection.INCREASING],
                    trending_down=trend_counts[TrendDirection.DECREASING],
                    stable_products=trend_counts[TrendDirection.STABLE],
                    volatile_products=trend_counts[TrendDirection.VOLATILE],
                    average_volatility=statistics.mean(volatilities) if volatilities else 0,
                    market_sentiment=market_sentiment,
                    hot_products=hot_products[:10],  # Top 10
                    declining_products=declining_products[:10],  # Top 10
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Failed to generate market overview: {e}")
            return MarketOverview(
                total_products=0,
                trending_up=0,
                trending_down=0,
                stable_products=0,
                volatile_products=0,
                average_volatility=0,
                market_sentiment=MarketSentiment.NEUTRAL,
                hot_products=[],
                declining_products=[],
                timestamp=datetime.utcnow()
            )

# Global pricing engine instance
pricing_engine = PricingIntelligenceEngine()