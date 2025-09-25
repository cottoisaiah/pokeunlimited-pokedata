"""
🎯 Analytics API
Advanced market intelligenc    try:
        async with TCGdexClient() as TCGDex_client:
            pokemon_service = TCGdexPokemonService(TCGDex_client)
            trending_cards = await pokemon_service.get_trending_cards(limit)
            
            # Enhance with eBay data
            enhanced_results = []ning TCGdex and eBay data
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
import asyncio
import structlog

from app.models.user_models import User
from app.core.security import get_current_user
from app.services.tcgdex_service import TCGdexClient, TCGdexPokemonService, Language
from app.services.ebay_service import EnhancedeBayService

logger = structlog.get_logger(__name__)
router = APIRouter()

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
import structlog

from app.models.user_models import User
from app.core.security import get_current_user
from app.services.tcgdex_service import TCGdexClient, TCGdexPokemonService, Language
from app.services.ebay_service import EnhancedeBayService
from app.services.cache_service import cache_service

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/trending")
async def get_trending_cards(
    limit: int = Query(20, ge=1, le=100, description="Number of trending cards to return"),
    time_period: str = Query("7d", regex="^(1d|7d|30d)$", description="Time period for trending analysis"),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get trending Pokemon cards based on TCGdex and eBay activity"""
    
    cache_key = f"analytics:trending:{limit}:{time_period}"
    cached_result = await cache_service.get(cache_key, prefix="analytics")
    
    if cached_result:
        logger.info("Returning cached trending analysis")
        return cached_result
    
    try:
        async with TCGdexClient() as tcgdx_client:
            pokemon_service = TCGdexPokemonService(tcgdx_client)
            trending_cards = await pokemon_service.get_trending_cards(limit)
            
            # Enhance with eBay data
            enhanced_results = []
            async with EnhancedeBayService() as ebay:
                for card in trending_cards:
                    # Get eBay market data for comparison
                    ebay_search = await ebay.search_pokemon_cards(
                        query=card.name,
                        limit=10
                    )
                    
                    # Calculate arbitrage opportunity
                    tcgdx_price = pokemon_service._get_market_price(card) or 0
                    avg_ebay_price = 0
                    
                    if ebay_search.listings:
                        ebay_prices = [listing.price for listing in ebay_search.listings if listing.price]
                        avg_ebay_price = sum(ebay_prices) / len(ebay_prices) if ebay_prices else 0
                    
                    profit_margin = 0
                    if tcgdx_price > 0 and avg_ebay_price > tcgdx_price:
                        profit_margin = ((avg_ebay_price - tcgdx_price) / tcgdx_price) * 100
                    
                    enhanced_results.append({
                        "card_id": card.id,
                        "name": card.name,
                        "set_name": card.set_name,
                        "rarity": card.rarity,
                        "image": card.image,
                        "pricing": {
                            "tcgdx_market": tcgdx_price,
                            "ebay_average": avg_ebay_price,
                            "arbitrage_margin": profit_margin
                        },
                        "market_score": pokemon_service._calculate_investment_score(card),
                        "last_updated": datetime.now().isoformat()
                    })
            
            result = {
                "trending_cards": enhanced_results,
                "time_period": time_period,
                "total_count": len(enhanced_results),
                "generated_at": datetime.now().isoformat()
            }
            
            # Cache for 10 minutes
            await cache_service.set(cache_key, result, ttl=600, prefix="analytics")
            
            logger.info(f"Generated trending analysis with {len(enhanced_results)} cards")
            return result
            
    except Exception as e:
        logger.error("Failed to generate trending analysis", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")

@router.get("/arbitrage")
async def analyze_arbitrage_opportunities(
    query: str = Query(..., min_length=2, description="Pokemon card search query"),
    min_profit: float = Query(5.0, ge=0, description="Minimum profit threshold"),
    current_user: User = Depends(get_current_user)
):
    """Analyze arbitrage opportunities between TCGdx and eBay markets"""
    
    if current_user.subscription_tier == "free":
        raise HTTPException(status_code=403, detail="Arbitrage analysis requires paid subscription")
    
    cache_key = f"analytics:arbitrage:{query}:{min_profit}"
    cached_result = await cache_service.get(cache_key, prefix="analytics")
    
    if cached_result:
        return cached_result
    
    try:
        opportunities = []
        
        async with TCGdexClient() as tcgdx_client:
            pokemon_service = TCGdexPokemonService(tcgdx_client)
            cards = await pokemon_service.search_pokemon_cards(query, limit=50)
            
            async with EnhancedeBayService() as ebay:
                for card in cards:
                    tcgdx_price = pokemon_service._get_market_price(card)
                    if not tcgdx_price or tcgdx_price < 5:  # Skip low-value cards
                        continue
                    
                    # Search eBay for similar cards
                    ebay_result = await ebay.search_pokemon_cards(
                        query=f"{card.name} {card.set_name}",
                        limit=20
                    )
                    
                    if ebay_result.listings:
                        # Calculate average sold price
                        recent_sales = [l.price for l in ebay_result.listings if l.price and l.price > 0]
                        if recent_sales:
                            avg_ebay_price = sum(recent_sales) / len(recent_sales)
                            potential_profit = avg_ebay_price - tcgdx_price
                            
                            if potential_profit >= min_profit:
                                profit_margin = (potential_profit / tcgdx_price) * 100
                                
                                opportunities.append({
                                    "card": {
                                        "id": card.id,
                                        "name": card.name,
                                        "set_name": card.set_name,
                                        "rarity": card.rarity,
                                        "image": card.image
                                    },
                                    "pricing": {
                                        "tcgdx_price": tcgdx_price,
                                        "ebay_average": avg_ebay_price,
                                        "potential_profit": potential_profit,
                                        "profit_margin": profit_margin
                                    },
                                    "market_data": {
                                        "ebay_listings_count": len(recent_sales),
                                        "confidence_score": min(len(recent_sales) * 10, 100)  # More listings = higher confidence
                                    }
                                })
        
        # Sort by potential profit
        opportunities.sort(key=lambda x: x["pricing"]["potential_profit"], reverse=True)
        
        result = {
            "opportunities": opportunities,
            "query": query,
            "min_profit_threshold": min_profit,
            "total_opportunities": len(opportunities),
            "generated_at": datetime.now().isoformat()
        }
        
        # Cache for 5 minutes (arbitrage data should be fresh)
        await cache_service.set(cache_key, result, ttl=300, prefix="analytics")
        
        logger.info(f"Found {len(opportunities)} arbitrage opportunities for '{query}'")
        return result
        
    except Exception as e:
        logger.error("Arbitrage analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Arbitrage analysis failed: {str(e)}")

@router.get("/market-overview")
async def get_market_overview(
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get comprehensive market overview combining all data sources"""
    
    cache_key = "analytics:market_overview"
    cached_result = await cache_service.get(cache_key, prefix="analytics")
    
    if cached_result:
        return cached_result
    
    try:
        async with TCGdexClient() as tcgdx_client:
            pokemon_service = TCGdexPokemonService(tcgdx_client)
            
            # Get trending cards
            trending = await pokemon_service.get_trending_cards(10)
            
            # Calculate market metrics
            total_market_value = sum(
                pokemon_service._get_market_price(card) or 0 
                for card in trending
            )
            
            avg_market_price = total_market_value / len(trending) if trending else 0
            
            # Get popular sets
            sets = await tcgdx_client.get_sets()
            recent_sets = sorted(sets, key=lambda s: s.release_date, reverse=True)[:5]
            
            result = {
                "market_summary": {
                    "trending_cards_count": len(trending),
                    "average_market_price": avg_market_price,
                    "total_tracked_value": total_market_value,
                    "active_sets": len(sets)
                },
                "trending_highlights": [
                    {
                        "name": card.name,
                        "set": card.set_name,
                        "price": pokemon_service._get_market_price(card),
                        "rarity": card.rarity
                    }
                    for card in trending[:5]
                ],
                "recent_sets": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "release_date": s.release_date,
                        "card_count": s.card_count
                    }
                    for s in recent_sets
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache for 15 minutes
            await cache_service.set(cache_key, result, ttl=900, prefix="analytics")
            
            return result
            
    except Exception as e:
        logger.error("Market overview generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Market overview failed: {str(e)}")

from fastapi import APIRouter, Depends, HTTPException
import structlog

from app.models.user_models import User
from app.core.security import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/dashboard")
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get user analytics dashboard data"""
    
    # Placeholder implementation
    return {
        "message": "Analytics dashboard - Coming soon!",
        "user_tier": current_user.subscription_tier
    }