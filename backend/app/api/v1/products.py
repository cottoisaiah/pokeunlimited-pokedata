"""
🎯 Products API
Comprehensive Pokemon product catalog endpoints
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
import structlog

from app.models.database import get_db_session
from app.models.product_models import Product, ProductPricing, PriceHistory
from app.models.user_models import User
from app.core.security import get_current_user_optional
from app.services.cache_service import cache_service
from app.services.tcgdex_service import TCGdexClient, TCGdexPokemonService, Language
from app.services.ebay_service import EnhancedeBayService
from app.schemas.product_schemas import (
    ProductResponse, ProductListResponse, ProductPricingResponse,
    PriceHistoryResponse, ProductSearchFilters
)

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=ProductListResponse)
async def get_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    set_name: Optional[str] = Query(None, description="Filter by set name"),
    rarity: Optional[str] = Query(None, description="Filter by rarity"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    is_tracked: Optional[bool] = Query(None, description="Filter by tracking status"),
    search: Optional[str] = Query(None, description="Search in product names"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get products with filtering, pagination, and sorting"""
    
    # Cache key for this query
    cache_key = f"products:list:{skip}:{limit}:{set_name}:{rarity}:{product_type}:{is_tracked}:{search}:{sort_by}:{sort_order}"
    
    # Try cache first
    cached_result = await cache_service.get(cache_key, prefix="product")
    if cached_result:
        logger.info("Returning cached product list")
        return cached_result
    
    try:
        async with get_db_session() as db:
            # Build base query
            query = select(Product).options(
                selectinload(Product.pricing)
            )
            
            # Apply filters
            conditions = []
            
            if set_name:
                conditions.append(Product.set_name.ilike(f"%{set_name}%"))
            
            if rarity:
                conditions.append(Product.rarity == rarity)
            
            if product_type:
                conditions.append(Product.product_type == product_type)
            
            if is_tracked is not None:
                conditions.append(Product.is_tracked == is_tracked)
            
            if search:
                search_conditions = or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.set_name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%")
                )
                conditions.append(search_conditions)
            
            # Only show active products
            conditions.append(Product.is_active == True)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count()).select_from(Product)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # Apply sorting
            sort_column = getattr(Product, sort_by, Product.name)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await db.execute(query)
            products = result.scalars().all()
            
            # Convert to response format
            product_responses = []
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
                    "last_price_update": product.last_price_update,
                    "created_at": product.created_at,
                    "pricing": None
                }
                
                # Add pricing data if available
                if product.pricing:
                    product_data["pricing"] = {
                        "market_price": float(product.pricing.market_price) if product.pricing.market_price else None,
                        "tcgplayer_market_price": float(product.pricing.tcgplayer_market_price) if product.pricing.tcgplayer_market_price else None,
                        "ebay_average_price": float(product.pricing.ebay_average_price) if product.pricing.ebay_average_price else None,
                        "confidence_score": product.pricing.confidence_score,
                        "last_updated": product.pricing.tcgplayer_last_updated or product.pricing.ebay_last_updated
                    }
                
                product_responses.append(product_data)
            
            response = {
                "items": product_responses,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < total
            }
            
            # Cache the response
            await cache_service.set(
                cache_key,
                response,
                ttl=300,  # 5 minutes for product lists
                prefix="product"
            )
            
            logger.info(f"Retrieved {len(products)} products")
            return response
            
    except Exception as e:
        logger.error(f"Failed to get products: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve products")

@router.get("/sets", response_model=List[Dict[str, Any]])
async def get_sets(
    limit: int = Query(100, ge=1, le=500, description="Number of sets to return"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get all available Pokemon sets"""
    
    cache_key = f"products:sets:{limit}"
    
    # Try cache first
    cached_result = await cache_service.get(cache_key, prefix="product")
    if cached_result:
        return cached_result
    
    try:
        async with get_db_session() as db:
            query = (
                select(
                    Product.set_name,
                    func.count(Product.id).label("product_count"),
                    func.min(Product.created_at).label("first_added"),
                    func.max(Product.last_price_update).label("last_updated")
                )
                .where(Product.is_active == True)
                .group_by(Product.set_name)
                .order_by(func.count(Product.id).desc())
                .limit(limit)
            )
            
            result = await db.execute(query)
            sets_data = result.all()
            
            sets = [
                {
                    "name": row.set_name,
                    "product_count": row.product_count,
                    "first_added": row.first_added,
                    "last_updated": row.last_updated
                }
                for row in sets_data
                if row.set_name  # Filter out null set names
            ]
            
            # Cache the response
            await cache_service.set(
                cache_key,
                sets,
                ttl=3600,  # 1 hour for sets
                prefix="product"
            )
            
            logger.info(f"Retrieved {len(sets)} Pokemon sets")
            return sets
            
    except Exception as e:
        logger.error(f"Failed to get sets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sets")

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int = Path(..., description="Product ID"),
    include_pricing: bool = Query(True, description="Include pricing data"),
    include_history: bool = Query(False, description="Include price history"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a specific product by ID"""
    
    cache_key = f"products:detail:{product_id}:{include_pricing}:{include_history}"
    
    # Try cache first
    cached_result = await cache_service.get(cache_key, prefix="product")
    if cached_result:
        return cached_result
    
    try:
        async with get_db_session() as db:
            # Build query with optional includes
            query = select(Product)
            
            if include_pricing:
                query = query.options(selectinload(Product.pricing))
            
            query = query.where(Product.id == product_id, Product.is_active == True)
            
            result = await db.execute(query)
            product = result.scalar_one_or_none()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Build response
            response = {
                "id": product.id,
                "name": product.name,
                "set_name": product.set_name,
                "number": product.number,
                "rarity": product.rarity,
                "product_type": product.product_type,
                "description": product.description,
                "image_url": product.image_url,
                "tcgplayer_id": product.tcgplayer_id,
                "tcgplayer_url": product.tcgplayer_url,
                "is_tracked": product.is_tracked,
                "last_price_update": product.last_price_update,
                "created_at": product.created_at,
                "updated_at": product.updated_at
            }
            
            # Add pricing data
            if include_pricing and product.pricing:
                response["pricing"] = {
                    "market_price": float(product.pricing.market_price) if product.pricing.market_price else None,
                    "tcgplayer_market_price": float(product.pricing.tcgplayer_market_price) if product.pricing.tcgplayer_market_price else None,
                    "tcgplayer_low_price": float(product.pricing.tcgplayer_low_price) if product.pricing.tcgplayer_low_price else None,
                    "tcgplayer_mid_price": float(product.pricing.tcgplayer_mid_price) if product.pricing.tcgplayer_mid_price else None,
                    "tcgplayer_high_price": float(product.pricing.tcgplayer_high_price) if product.pricing.tcgplayer_high_price else None,
                    "ebay_average_price": float(product.pricing.ebay_average_price) if product.pricing.ebay_average_price else None,
                    "ebay_low_price": float(product.pricing.ebay_low_price) if product.pricing.ebay_low_price else None,
                    "ebay_high_price": float(product.pricing.ebay_high_price) if product.pricing.ebay_high_price else None,
                    "confidence_score": product.pricing.confidence_score,
                    "tcgplayer_last_updated": product.pricing.tcgplayer_last_updated,
                    "ebay_last_updated": product.pricing.ebay_last_updated
                }
            
            # Add price history
            if include_history:
                history_query = (
                    select(PriceHistory)
                    .where(PriceHistory.product_id == product_id)
                    .order_by(PriceHistory.timestamp.desc())
                    .limit(30)  # Last 30 data points
                )
                
                history_result = await db.execute(history_query)
                price_history = history_result.scalars().all()
                
                response["price_history"] = [
                    {
                        "timestamp": h.timestamp,
                        "price": float(h.price),
                        "source": h.source,
                        "price_type": h.price_type
                    }
                    for h in price_history
                ]
            
            # Cache the response
            await cache_service.set(
                cache_key,
                response,
                ttl=300,  # 5 minutes for product details
                prefix="product"
            )
            
            logger.info(f"Retrieved product {product_id}: {product.name}")
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve product")

@router.get("/{product_id}/pricing", response_model=ProductPricingResponse)
async def get_product_pricing(
    product_id: int = Path(..., description="Product ID"),
    refresh: bool = Query(False, description="Force refresh from external APIs"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get current pricing data for a product"""
    
    if not refresh:
        cache_key = f"products:pricing:{product_id}"
        cached_result = await cache_service.get(cache_key, prefix="pricing")
        if cached_result:
            return cached_result
    
    try:
        async with get_db_session() as db:
            # Get product
            product_query = select(Product).where(
                Product.id == product_id,
                Product.is_active == True
            )
            product_result = await db.execute(product_query)
            product = product_result.scalar_one_or_none()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Get current pricing
            pricing_query = select(ProductPricing).where(
                ProductPricing.product_id == product_id
            )
            pricing_result = await db.execute(pricing_query)
            pricing = pricing_result.scalar_one_or_none()
            
            response = {
                "product_id": product_id,
                "product_name": product.name,
                "last_updated": None,
                "pricing_data": {}
            }
            
            if pricing:
                response["pricing_data"] = {
                    "market_price": float(pricing.market_price) if pricing.market_price else None,
                    "confidence_score": pricing.confidence_score,
                    "tcgplayer": {
                        "market_price": float(pricing.tcgplayer_market_price) if pricing.tcgplayer_market_price else None,
                        "low_price": float(pricing.tcgplayer_low_price) if pricing.tcgplayer_low_price else None,
                        "mid_price": float(pricing.tcgplayer_mid_price) if pricing.tcgplayer_mid_price else None,
                        "high_price": float(pricing.tcgplayer_high_price) if pricing.tcgplayer_high_price else None,
                        "last_updated": pricing.tcgplayer_last_updated
                    },
                    "ebay": {
                        "average_price": float(pricing.ebay_average_price) if pricing.ebay_average_price else None,
                        "low_price": float(pricing.ebay_low_price) if pricing.ebay_low_price else None,
                        "high_price": float(pricing.ebay_high_price) if pricing.ebay_high_price else None,
                        "listing_count": pricing.ebay_listing_count,
                        "last_updated": pricing.ebay_last_updated
                    }
                }
                response["last_updated"] = max(
                    filter(None, [pricing.tcgplayer_last_updated, pricing.ebay_last_updated])
                ) if any([pricing.tcgplayer_last_updated, pricing.ebay_last_updated]) else None
            
            # If refresh requested or no recent data, fetch from APIs
            if refresh or not pricing or (
                response["last_updated"] and 
                (datetime.utcnow() - response["last_updated"]).total_seconds() > 3600
            ):
                # This would trigger background price updates
                # For now, return current data
                pass
            
            # Cache the response
            await cache_service.set(
                f"products:pricing:{product_id}",
                response,
                ttl=600,  # 10 minutes for pricing data
                prefix="pricing"
            )
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pricing for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pricing data")

@router.get("/{product_id}/history", response_model=PriceHistoryResponse)
async def get_price_history(
    product_id: int = Path(..., description="Product ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    source: Optional[str] = Query(None, description="Filter by price source"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get price history for a product"""
    
    cache_key = f"products:history:{product_id}:{days}:{source}"
    
    # Try cache first
    cached_result = await cache_service.get(cache_key, prefix="pricing")
    if cached_result:
        return cached_result
    
    try:
        async with get_db_session() as db:
            # Verify product exists
            product_query = select(Product).where(
                Product.id == product_id,
                Product.is_active == True
            )
            product_result = await db.execute(product_query)
            product = product_result.scalar_one_or_none()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Build history query
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = (
                select(PriceHistory)
                .where(
                    PriceHistory.product_id == product_id,
                    PriceHistory.timestamp >= start_date
                )
                .order_by(PriceHistory.timestamp.asc())
            )
            
            if source:
                query = query.where(PriceHistory.source == source)
            
            result = await db.execute(query)
            history = result.scalars().all()
            
            # Group by source
            sources_data = {}
            for record in history:
                if record.source not in sources_data:
                    sources_data[record.source] = []
                
                sources_data[record.source].append({
                    "timestamp": record.timestamp,
                    "price": float(record.price),
                    "price_type": record.price_type
                })
            
            response = {
                "product_id": product_id,
                "product_name": product.name,
                "period_days": days,
                "data_points": len(history),
                "sources": sources_data
            }
            
            # Cache the response
            await cache_service.set(
                cache_key,
                response,
                ttl=1800,  # 30 minutes for history data
                prefix="pricing"
            )
            
            logger.info(f"Retrieved {len(history)} price history records for product {product_id}")
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get price history for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve price history")

@router.get("/{product_id}/market-insights")
async def get_market_insights(
    product_id: int = Path(..., description="Product ID"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get comprehensive market insights for a product"""
    
    cache_key = f"products:insights:{product_id}"
    
    # Try cache first
    cached_result = await cache_service.get(cache_key, prefix="analytics")
    if cached_result:
        return cached_result
    
    try:
        async with get_db_session() as db:
            # Get product
            product_query = select(Product).where(
                Product.id == product_id,
                Product.is_active == True
            )
            product_result = await db.execute(product_query)
            product = product_result.scalar_one_or_none()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Get market insights from eBay
            ebay_insights = await ebay_service.get_market_insights(
                product.name,
                product.set_name
            )
            
            response = {
                "product_id": product_id,
                "product_name": product.name,
                "set_name": product.set_name,
                "insights": ebay_insights,
                "generated_at": datetime.utcnow()
            }
            
            # Cache the response
            await cache_service.set(
                cache_key,
                response,
                ttl=3600,  # 1 hour for market insights
                prefix="analytics"
            )
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get market insights for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve market insights")