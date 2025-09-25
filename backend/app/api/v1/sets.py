"""
🎯 Set Collections API
Pokemon TCG set collection endpoints matching pokedata.io structure
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlalchemy import func, or_
import structlog

from app.models.database import get_db_session
from app.models.product_models import ProductSet, Product, ProductPricing
from app.models.user_models import User
from app.core.security import get_current_user_optional
from app.services.tcgdex_data_fetcher import TcgdexDataFetcher, sync_tcgdex_data, sync_single_set
from app.schemas.set_schemas import (
    SetCollection, SetSummary, SetCard, SetListResponse, 
    SetFilters, UserSetProgress
)

logger = structlog.get_logger(__name__)
router = APIRouter()

# TCGdex specific router
tcgdex_router = APIRouter()


@router.get("/", response_model=SetListResponse)
async def get_sets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term"),
    series: Optional[str] = Query(None, description="Filter by series"),
    format: Optional[str] = Query(None, description="Legal format filter"),
    release_year: Optional[int] = Query(None, description="Release year filter"),
    sort_by: str = Query("release_date", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get paginated list of Pokemon TCG sets"""
    async with get_db_session() as db:
        # Build query
        query = db.query(ProductSet)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    ProductSet.name.ilike(f"%{search}%"),
                    ProductSet.code.ilike(f"%{search}%"),
                    ProductSet.series.ilike(f"%{search}%")
                )
            )
        
        if series:
            query = query.filter(ProductSet.series.ilike(f"%{series}%"))
        
        if format == "standard" and release_year:
            # Simple standard legality check (last 2 years)
            current_year = 2025
            if release_year >= current_year - 2:
                query = query.filter(ProductSet.is_standard_legal == True)
        
        if release_year:
            query = query.filter(func.extract('year', ProductSet.release_date) == release_year)
        
        # Apply sorting
        sort_column = getattr(ProductSet, sort_by, ProductSet.release_date)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        sets = query.offset(skip).limit(limit).all()
        
        # Convert to response format
        set_summaries = []
        for set_obj in sets:
            # Calculate set statistics
            card_count = db.query(Product).filter(Product.set_id == set_obj.id).count()
            
            set_summary = SetSummary(
                id=set_obj.id,
                name=set_obj.name,
                code=set_obj.code,
                series=set_obj.series,
                symbol_url=set_obj.symbol_url,
                logo_url=set_obj.logo_url,
                release_date=set_obj.release_date,
                total_cards=card_count,
                avg_card_price=float(set_obj.avg_card_price) if set_obj.avg_card_price else None,
                set_market_cap=float(set_obj.set_market_cap) if set_obj.set_market_cap else None,
                completion_cost=float(set_obj.completion_cost) if set_obj.completion_cost else None,
                cards_owned=0,  # TODO: Calculate based on user collection
                completion_percentage=0.0  # TODO: Calculate based on user collection
            )
            set_summaries.append(set_summary)
        
        return SetListResponse(
            items=set_summaries,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + len(sets) < total
        )


@router.get("/{set_id}", response_model=SetCollection)
async def get_set_collection(
    set_id: int,
    sort_by: str = Query("number", description="Sort cards by field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    rarity_filter: Optional[str] = Query(None, description="Filter by rarity"),
    owned_only: bool = Query(False, description="Show only owned cards"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get complete set collection view with cards (matching pokedata.io)"""
    async with get_db_session() as db:
        # Get set information
        set_obj = db.query(ProductSet).filter(ProductSet.id == set_id).first()
        if not set_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Set not found"
            )
        
        # Get cards in the set with pricing data
        cards_query = db.query(Product).options(
            selectinload(Product.pricing_data)
        ).filter(Product.set_id == set_id)
        
        # Apply rarity filter
        if rarity_filter:
            cards_query = cards_query.filter(Product.rarity.ilike(f"%{rarity_filter}%"))
        
        # Apply sorting
        if sort_by == "number":
            # Sort by card number (handle numeric sorting)
            if sort_order == "asc":
                cards_query = cards_query.order_by(Product.number.asc())
            else:
                cards_query = cards_query.order_by(Product.number.desc())
        else:
            sort_column = getattr(Product, sort_by, Product.name)
            if sort_order == "desc":
                cards_query = cards_query.order_by(sort_column.desc())
            else:
                cards_query = cards_query.order_by(sort_column.asc())
        
        cards = cards_query.all()
        
        # Convert cards to SetCard format
        set_cards = []
        total_value = 0.0
        cards_owned = 0
        secret_rares_owned = 0
        secret_rares_total = 0
        
        for card in cards:
            # Get current pricing
            current_price = None
            pricing_data = None
            
            if card.pricing_data:
                latest_pricing = card.pricing_data[0]  # Assuming first is latest
                current_price = float(latest_pricing.market_price) if latest_pricing.market_price else None
                if current_price:
                    total_value += current_price
            
            # Count secret rares
            if card.rarity and "secret" in card.rarity.lower():
                secret_rares_total += 1
                # TODO: Check if owned
            
            set_card = SetCard(
                id=card.id,
                name=card.name,
                number=card.number,
                rarity=card.rarity,
                image_url=card.image_url,
                hp=card.hp,
                pokemon_type=card.pokemon_type,
                stage=card.stage,
                current_price=current_price,
                price_trend="stable",  # TODO: Calculate from price history
                is_owned=False,  # TODO: Check user collection
                condition=None,
                purchase_price=None
            )
            set_cards.append(set_card)
        
        # Calculate completion statistics
        total_cards = len(cards)
        completion_percentage = (cards_owned / total_cards * 100) if total_cards > 0 else 0
        
        return SetCollection(
            id=set_obj.id,
            name=set_obj.name,
            code=set_obj.code,
            series=set_obj.series or "Unknown Series",
            symbol=set_obj.code,
            release_date=set_obj.release_date,
            description=set_obj.description,
            logo_url=set_obj.logo_url,
            symbol_url=set_obj.symbol_url,
            total_value=total_value,
            completion_percentage=completion_percentage,
            total_cards=total_cards,
            cards_owned=cards_owned,
            cards_missing=total_cards - cards_owned,
            secret_rares_owned=secret_rares_owned,
            secret_rares_total=secret_rares_total,
            cards=set_cards
        )


@router.get("/series/{series_name}")
async def get_sets_by_series(
    series_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get all sets in a specific series"""
    async with get_db_session() as db:
        query = db.query(ProductSet).filter(
            ProductSet.series.ilike(f"%{series_name}%")
        ).order_by(ProductSet.release_date.desc())
        
        total = query.count()
        sets = query.offset(skip).limit(limit).all()
        
        return {
            "series": series_name,
            "sets": [
                {
                    "id": s.id,
                    "name": s.name,
                    "code": s.code,
                    "release_date": s.release_date,
                    "total_cards": s.total_cards,
                    "symbol_url": s.symbol_url
                }
                for s in sets
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }


@router.get("/{set_id}/stats")
async def get_set_statistics(
    set_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get detailed set statistics and market data"""
    async with get_db_session() as db:
        set_obj = db.query(ProductSet).filter(ProductSet.id == set_id).first()
        if not set_obj:
            raise HTTPException(status_code=404, detail="Set not found")
        
        # Calculate real-time statistics
        cards_query = db.query(Product).filter(Product.set_id == set_id)
        
        total_cards = cards_query.count()
        rarity_breakdown = db.query(
            Product.rarity, 
            func.count(Product.id)
        ).filter(Product.set_id == set_id).group_by(Product.rarity).all()
        
        # Price statistics
        price_stats = db.query(
            func.avg(ProductPricing.market_price).label('avg_price'),
            func.min(ProductPricing.market_price).label('min_price'),
            func.max(ProductPricing.market_price).label('max_price'),
            func.sum(ProductPricing.market_price).label('total_value')
        ).join(Product).filter(Product.set_id == set_id).first()
        
        return {
            "set_id": set_id,
            "name": set_obj.name,
            "total_cards": total_cards,
            "rarity_breakdown": dict(rarity_breakdown),
            "price_statistics": {
                "average_price": float(price_stats.avg_price) if price_stats.avg_price else 0,
                "minimum_price": float(price_stats.min_price) if price_stats.min_price else 0,
                "maximum_price": float(price_stats.max_price) if price_stats.max_price else 0,
                "total_value": float(price_stats.total_value) if price_stats.total_value else 0
            },
            "market_cap": float(set_obj.set_market_cap) if set_obj.set_market_cap else 0,
            "completion_cost": float(set_obj.completion_cost) if set_obj.completion_cost else 0
        }


@router.post("/sync")
async def sync_all_sets_from_tcgdex(
    limit: Optional[int] = Query(None, description="Limit number of sets to sync"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Sync all Pokemon TCG sets from live TCGdex API"""
    try:
        logger.info(f"Starting TCGdex data sync (limit: {limit})")
        synced_count = await sync_tcgdex_data(limit=limit)
        
        return {
            "status": "success",
            "message": f"Successfully synced {synced_count} sets from TCGdex API",
            "synced_sets": synced_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to sync TCGdex data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync data from TCGdex API: {str(e)}"
        )


@router.post("/{set_id}/sync")
async def sync_single_set_from_tcgdex(
    set_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Sync a specific set from TCGdex API"""
    try:
        logger.info(f"Starting sync for set {set_id} from TCGdex API")
        success = await sync_single_set(set_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Successfully synced set {set_id} from TCGdex API",
                "set_id": set_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Set {set_id} not found in TCGdex API or sync failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync set {set_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync set from TCGdex API: {str(e)}"
        )


@tcgdex_router.get("/tcgdex/available")
async def get_available_tcgdex_sets():
    """Get all available sets from TCGdex API without syncing to database"""
    try:
        async with TcgdexDataFetcher() as fetcher:
            sets_data = await fetcher.fetch_all_sets()
            
            return {
                "status": "success",
                "total_sets": len(sets_data),
                "sets": [
                    {
                        "id": s.get('id'),
                        "name": s.get('name'),
                        "series": s.get('serie', {}).get('name'),
                        "release_date": s.get('releaseDate'),
                        "card_count": s.get('cardCount', {}).get('total', 0),
                        "symbol": s.get('symbol'),
                        "logo": s.get('logo')
                    }
                    for s in sets_data
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to fetch available TCGdex sets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch data from TCGdex API: {str(e)}"
        )


@tcgdex_router.get("/tcgdex/sets")
async def get_tcgdex_sets():
    """Get all TCGdex sets"""
    try:
        async with TcgdexDataFetcher() as fetcher:
            sets_data = await fetcher.fetch_all_sets()
            return {
                "status": "success",
                "data": sets_data
            }
    except Exception as e:
        logger.error(f"Failed to fetch TCGdex sets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch TCGdex sets: {str(e)}"
        )


@tcgdex_router.get("/tcgdex/sets/{set_id}")
async def get_tcgdex_set_details(set_id: str):
    """Get TCGdex set details"""
    try:
        async with TcgdexDataFetcher() as fetcher:
            set_data = await fetcher.fetch_set_details(set_id)
            if not set_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Set {set_id} not found in TCGdex API"
                )
            return {
                "status": "success",
                "data": set_data
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch TCGdex set {set_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch TCGdex set details: {str(e)}"
        )


@tcgdex_router.get("/tcgdex/sets/{set_id}/cards")
async def get_tcgdex_set_cards(set_id: str):
    """Get all cards from a TCGdex set"""
    try:
        async with TcgdexDataFetcher() as fetcher:
            cards_data = await fetcher.fetch_set_cards(set_id)
            return {
                "status": "success",
                "data": cards_data
            }
    except Exception as e:
        logger.error(f"Failed to fetch TCGdex cards for set {set_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch TCGdex cards: {str(e)}"
        )