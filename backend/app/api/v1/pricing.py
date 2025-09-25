"""
🎯 Pricing API
Advanced pricing intelligence and market analysis endpoints
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
import structlog

from app.models.user_models import User
from app.core.security import get_current_user
from app.services.pricing_engine import pricing_engine

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/analysis/{product_id}")
async def get_pricing_analysis(
    product_id: int = Path(..., description="Product ID"),
    days_back: int = Query(30, ge=7, le=365, description="Days of history to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive pricing analysis for a product"""
    
    # Check user tier access
    if current_user.subscription_tier == "free":
        raise HTTPException(status_code=403, detail="Pricing analysis requires paid subscription")
    
    try:
        analysis = await pricing_engine.analyze_product_pricing(product_id, days_back)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Product not found or insufficient data")
        
        return {
            "product_id": analysis.product_id,
            "product_name": analysis.product_name,
            "current_price": analysis.current_price,
            "price_confidence": analysis.price_confidence,
            "trend": {
                "direction": analysis.trend_direction.value,
                "strength": analysis.trend_strength,
                "velocity": analysis.price_velocity
            },
            "market_sentiment": {
                "sentiment": analysis.market_sentiment.value,
                "score": analysis.sentiment_score
            },
            "risk_metrics": {
                "volatility": analysis.price_volatility,
                "support_level": analysis.support_level,
                "resistance_level": analysis.resistance_level
            },
            "recommendations": {
                "buy": analysis.buy_recommendation,
                "sell": analysis.sell_recommendation,
                "target_price": analysis.target_price
            },
            "external_data": {
                "tcgplayer": analysis.tcgplayer_data,
                "ebay": analysis.ebay_data
            },
            "metadata": {
                "analysis_timestamp": analysis.analysis_timestamp,
                "data_points_count": analysis.data_points_count
            }
        }
        
    except Exception as e:
        logger.error(f"Pricing analysis failed for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Pricing analysis failed")

@router.get("/market-overview")
async def get_market_overview(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive market overview and trends"""
    
    # Platinum tier feature
    if current_user.subscription_tier not in ["platinum"]:
        raise HTTPException(status_code=403, detail="Market overview requires Platinum subscription")
    
    try:
        overview = await pricing_engine.generate_market_overview()
        
        return {
            "market_summary": {
                "total_products": overview.total_products,
                "trending_up": overview.trending_up,
                "trending_down": overview.trending_down,
                "stable_products": overview.stable_products,
                "volatile_products": overview.volatile_products,
                "average_volatility": overview.average_volatility,
                "market_sentiment": overview.market_sentiment.value
            },
            "hot_products": overview.hot_products,
            "declining_products": overview.declining_products,
            "timestamp": overview.timestamp
        }
        
    except Exception as e:
        logger.error(f"Market overview generation failed: {e}")
        raise HTTPException(status_code=500, detail="Market overview generation failed")