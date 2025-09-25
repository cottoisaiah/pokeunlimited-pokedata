"""
🎯 Search API
Advanced search capabilities across Pokemon products
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
import structlog

from app.models.database import get_db_session
from app.models.product_models import Product, ProductPricing
from app.models.user_models import User
from app.models.analytics_models import SearchQuery
from app.core.security import get_current_user_optional
from app.services.cache_service import cache_service
from app.services.tcgdex_service import tcgdex_service
from app.services.ebay_service import EnhancedeBayService

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/products")
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    include_pricing: bool = Query(True, description="Include pricing data"),
    set_filter: Optional[str] = Query(None, description="Filter by Pokemon set"),
    rarity_filter: Optional[str] = Query(None, description="Filter by rarity"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    sort_by: str = Query("relevance", description="Sort by field"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Search Pokemon products with advanced filtering"""
    
    # Normalize query
    normalized_query = q.strip().lower()
    
    # Track search query
    try:
        async with get_db_session() as db:
            search_record = SearchQuery(
                query_text=q,
                normalized_query=normalized_query,
                user_id=current_user.id if current_user else None,
                search_type="product",
                filters_applied={
                    "set_filter": set_filter,
                    "rarity_filter": rarity_filter,
                    "min_price": min_price,
                    "max_price": max_price
                },
                sort_order=sort_by
            )
            db.add(search_record)
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to track search query: {e}")
    
    # Check cache
    cache_key = f"search:products:{normalized_query}:{limit}:{offset}:{include_pricing}:{set_filter}:{rarity_filter}:{min_price}:{max_price}:{sort_by}"
    cached_result = await cache_service.get(cache_key, prefix="search")
    if cached_result:
        logger.info(f"Returning cached search results for: {q}")
        return cached_result
    
    try:
        async with get_db_session() as db:
            # Build search query
            query = select(Product)
            
            if include_pricing:
                query = query.options(selectinload(Product.pricing))
            
            # Search conditions
            search_conditions = or_(
                Product.name.ilike(f"%{q}%"),
                Product.set_name.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%"),
                Product.number.ilike(f"%{q}%")
            )
            
            conditions = [
                Product.is_active == True,
                search_conditions
            ]
            
            # Apply filters
            if set_filter:
                conditions.append(Product.set_name.ilike(f"%{set_filter}%"))
            
            if rarity_filter:
                conditions.append(Product.rarity == rarity_filter)
            
            # Price filters (join with pricing table)
            if min_price is not None or max_price is not None:
                query = query.join(ProductPricing, Product.id == ProductPricing.product_id, isouter=True)
                
                if min_price is not None:
                    conditions.append(ProductPricing.market_price >= min_price)
                
                if max_price is not None:
                    conditions.append(ProductPricing.market_price <= max_price)
            
            query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count()).select_from(Product)
            if min_price is not None or max_price is not None:
                count_query = count_query.join(ProductPricing, Product.id == ProductPricing.product_id, isouter=True)
            count_query = count_query.where(and_(*conditions))
            
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # Apply sorting
            if sort_by == "relevance":
                # Simple relevance scoring based on exact matches
                query = query.order_by(
                    func.case(
                        (Product.name.ilike(f"{q}%"), 1),
                        (Product.name.ilike(f"%{q}%"), 2),
                        else_=3
                    ),
                    Product.name.asc()
                )
            elif sort_by == "price_low":
                query = query.join(ProductPricing, Product.id == ProductPricing.product_id, isouter=True)
                query = query.order_by(ProductPricing.market_price.asc().nullslast())
            elif sort_by == "price_high":
                query = query.join(ProductPricing, Product.id == ProductPricing.product_id, isouter=True)
                query = query.order_by(ProductPricing.market_price.desc().nullsfirst())
            elif sort_by == "name":
                query = query.order_by(Product.name.asc())
            elif sort_by == "newest":
                query = query.order_by(Product.created_at.desc())
            else:
                query = query.order_by(Product.name.asc())
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await db.execute(query)
            products = result.scalars().all()
            
            # Format results
            results = []
            for product in products:
                product_data = {
                    "id": product.id,
                    "name": product.name,
                    "set_name": product.set_name,
                    "number": product.number,
                    "rarity": product.rarity,
                    "product_type": product.product_type,
                    "image_url": product.image_url,
                    "tcgplayer_id": product.tcgplayer_id,
                    "is_tracked": product.is_tracked,
                    "created_at": product.created_at
                }
                
                if include_pricing and product.pricing:
                    product_data["pricing"] = {
                        "market_price": float(product.pricing.market_price) if product.pricing.market_price else None,
                        "tcgplayer_market_price": float(product.pricing.tcgplayer_market_price) if product.pricing.tcgplayer_market_price else None,
                        "ebay_average_price": float(product.pricing.ebay_average_price) if product.pricing.ebay_average_price else None,
                        "confidence_score": product.pricing.confidence_score,
                        "last_updated": product.pricing.tcgplayer_last_updated or product.pricing.ebay_last_updated
                    }
                
                results.append(product_data)
            
            response = {
                "query": q,
                "total": total,
                "offset": offset,
                "limit": limit,
                "has_more": offset + limit < total,
                "results": results,
                "search_time_ms": 0,  # Would calculate actual search time
                "suggestions": []  # Would implement search suggestions
            }
            
            # Update search record with results
            try:
                search_record.total_results = total
                search_record.results_returned = len(results)
                await db.commit()
            except:
                pass
            
            # Cache results
            await cache_service.set(
                cache_key,
                response,
                ttl=300,  # 5 minutes
                prefix="search"
            )
            
            logger.info(f"Search for '{q}' returned {len(results)} results")
            return response
            
    except Exception as e:
        logger.error(f"Search failed for query '{q}': {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get search suggestions based on partial query"""
    
    cache_key = f"search:suggestions:{q.lower()}:{limit}"
    cached_result = await cache_service.get(cache_key, prefix="search")
    if cached_result:
        return cached_result
    
    try:
        async with get_db_session() as db:
            # Get product name suggestions
            name_query = (
                select(Product.name)
                .where(
                    Product.is_active == True,
                    Product.name.ilike(f"{q}%")
                )
                .order_by(Product.name.asc())
                .limit(limit // 2)
            )
            
            name_result = await db.execute(name_query)
            name_suggestions = [row[0] for row in name_result.fetchall()]
            
            # Get set name suggestions
            set_query = (
                select(Product.set_name)
                .where(
                    Product.is_active == True,
                    Product.set_name.ilike(f"{q}%"),
                    Product.set_name.isnot(None)
                )
                .group_by(Product.set_name)
                .order_by(Product.set_name.asc())
                .limit(limit // 2)
            )
            
            set_result = await db.execute(set_query)
            set_suggestions = [row[0] for row in set_result.fetchall()]
            
            suggestions = []
            
            # Add name suggestions
            for name in name_suggestions:
                suggestions.append({
                    "text": name,
                    "type": "product",
                    "category": "Product Name"
                })
            
            # Add set suggestions
            for set_name in set_suggestions:
                suggestions.append({
                    "text": set_name,
                    "type": "set",
                    "category": "Pokemon Set"
                })
            
            # Sort and limit
            suggestions = suggestions[:limit]
            
            response = {
                "query": q,
                "suggestions": suggestions
            }
            
            # Cache suggestions
            await cache_service.set(
                cache_key,
                response,
                ttl=3600,  # 1 hour for suggestions
                prefix="search"
            )
            
            return response
            
    except Exception as e:
        logger.error(f"Failed to get suggestions for '{q}': {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")

@router.get("/trending")
async def get_trending_searches(
    limit: int = Query(20, ge=1, le=100, description="Number of trending searches"),
    period_hours: int = Query(24, ge=1, le=168, description="Time period in hours"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get trending search queries"""
    
    cache_key = f"search:trending:{limit}:{period_hours}"
    cached_result = await cache_service.get(cache_key, prefix="search")
    if cached_result:
        return cached_result
    
    try:
        async with get_db_session() as db:
            # Get trending searches from the last period
            since_date = datetime.utcnow() - timedelta(hours=period_hours)
            
            query = (
                select(
                    SearchQuery.normalized_query,
                    func.count(SearchQuery.id).label("search_count"),
                    func.avg(SearchQuery.total_results).label("avg_results"),
                    func.max(SearchQuery.timestamp).label("last_searched")
                )
                .where(
                    SearchQuery.timestamp >= since_date,
                    SearchQuery.normalized_query.isnot(None)
                )
                .group_by(SearchQuery.normalized_query)
                .having(func.count(SearchQuery.id) >= 2)  # At least 2 searches
                .order_by(func.count(SearchQuery.id).desc())
                .limit(limit)
            )
            
            result = await db.execute(query)
            trending = result.all()
            
            trending_searches = [
                {
                    "query": row.normalized_query,
                    "search_count": row.search_count,
                    "avg_results": int(row.avg_results) if row.avg_results else 0,
                    "last_searched": row.last_searched
                }
                for row in trending
            ]
            
            response = {
                "period_hours": period_hours,
                "trending_searches": trending_searches,
                "generated_at": datetime.utcnow()
            }
            
            # Cache trending searches
            await cache_service.set(
                cache_key,
                response,
                ttl=1800,  # 30 minutes
                prefix="search"
            )
            
            return response
            
    except Exception as e:
        logger.error(f"Failed to get trending searches: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trending searches")

@router.get("/external/tcgdex")
async def search_tcgdex(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=250, description="Number of results"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Search TCGdex catalog directly (includes TCGPlayer pricing data)"""
    
    # Basic tier check - this would be more sophisticated in production
    if not current_user or current_user.subscription_tier == "free":
        raise HTTPException(status_code=403, detail="TCGdex search requires paid subscription")
    
    cache_key = f"search:tcgdex:{q.lower()}:{limit}"
    cached_result = await cache_service.get(cache_key, prefix="search")
    if cached_result:
        return cached_result
    
    try:
        # Use the global TCGdex service instance
        cards = await tcgdex_service.search_cards(
            query=q, 
            limit=limit
        )
        
        # Format response
        results = [
            {
                "tcgdex_id": card.id,
                "name": card.name,
                "set_name": card.set_name,
                "set_id": card.set_id,
                "rarity": card.rarity,
                "image_url": card.image_url,
                "hp": card.hp,
                "types": card.types,
                "pricing": {
                    "tcgplayer": card.tcgplayer_prices or {},
                    "cardmarket": card.cardmarket_prices or {}
                },
                "release_date": card.release_date,
                "local_id": card.local_id,
                "variants": card.variants,
                "source": "tcgdex"
            }
            for card in cards
        ]
        
        response = {
            "query": q,
            "total": len(results),
            "results": results,
            "source": "tcgdex"
        }
        
        # Cache results
        await cache_service.set(
            cache_key,
            response,
            ttl=1800,  # 30 minutes
            prefix="search"
        )
        
        return response
            
    except Exception as e:
        logger.error(f"TCGdex search failed for '{q}': {e}")
        raise HTTPException(status_code=500, detail="TCGdex search failed")

@router.get("/external/ebay")
async def search_ebay(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    condition: Optional[str] = Query(None, description="Condition filter"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Search eBay marketplace directly"""
    
    # Basic tier check
    if not current_user or current_user.subscription_tier == "free":
        raise HTTPException(status_code=403, detail="eBay search requires paid subscription")
    
    cache_key = f"search:ebay:{q.lower()}:{limit}:{condition}:{price_min}:{price_max}"
    cached_result = await cache_service.get(cache_key, prefix="search")
    if cached_result:
        return cached_result
    
    try:
        async with EnhancedeBayService() as ebay:
            search_result = await ebay.search_pokemon_cards(
                query=q,
                limit=limit,
                condition=condition,
                price_min=price_min,
                price_max=price_max
            )
            
            # Format response
            results = [
                {
                    "item_id": listing.item_id,
                    "title": listing.title,
                    "price": listing.price,
                    "condition": listing.condition,
                    "listing_type": listing.listing_type,
                    "image_url": listing.image_url,
                    "item_url": listing.item_url,
                    "seller": {
                        "username": listing.seller_username,
                        "feedback_score": listing.seller_feedback_score
                    },
                    "source": "ebay"
                }
                for listing in search_result.listings
            ]
            
            response = {
                "query": q,
                "total": search_result.total_count,
                "results": results,
                "analytics": {
                    "average_price": search_result.average_price,
                    "price_range": {
                        "min": search_result.price_range[0],
                        "max": search_result.price_range[1]
                    },
                    "condition_breakdown": search_result.condition_breakdown
                },
                "source": "ebay"
            }
            
            # Cache results
            await cache_service.set(
                cache_key,
                response,
                ttl=600,  # 10 minutes for eBay
                prefix="search"
            )
            
            return response
            
    except Exception as e:
        logger.error(f"eBay search failed for '{q}': {e}")
        raise HTTPException(status_code=500, detail="eBay search failed")