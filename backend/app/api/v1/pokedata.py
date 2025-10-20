"""
🎯 PokeData Direct Database Access API
Direct access to pokedata_cards and pokedata_sets tables with multi-language support
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import text
import structlog

from app.models.database import get_db_session

logger = structlog.get_logger(__name__)
router = APIRouter()

# Supported languages
SUPPORTED_LANGUAGES = [
    'en', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'nl', 
    'pl', 'pt_br', 'ru', 'th', 'zh_cn', 'zh_tw', 'id'
]

def validate_language(lang: str) -> str:
    """Validate and sanitize language parameter"""
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported language: {lang}. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    return lang


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages with their data counts"""
    try:
        async with get_db_session() as db:
            languages_info = []
            
            for lang in SUPPORTED_LANGUAGES:
                try:
                    # Get set and card counts for each language
                    sets_count_query = text(f"SELECT COUNT(*) FROM pokedata_sets_{lang}")
                    cards_count_query = text(f"SELECT COUNT(*) FROM pokedata_cards_{lang}")
                    
                    sets_result = await db.execute(sets_count_query)
                    cards_result = await db.execute(cards_count_query)
                    
                    sets_count = sets_result.scalar()
                    cards_count = cards_result.scalar()
                    
                    # Language display names
                    lang_names = {
                        'en': 'English', 'de': 'German', 'es': 'Spanish', 'fr': 'French',
                        'it': 'Italian', 'ja': 'Japanese', 'ko': 'Korean', 'nl': 'Dutch',
                        'pl': 'Polish', 'pt_br': 'Portuguese (Brazil)', 'ru': 'Russian',
                        'th': 'Thai', 'zh_cn': 'Chinese (Simplified)', 'zh_tw': 'Chinese (Traditional)',
                        'id': 'Indonesian'
                    }
                    
                    languages_info.append({
                        "code": lang,
                        "name": lang_names.get(lang, lang),
                        "sets_count": sets_count,
                        "cards_count": cards_count,
                        "has_data": sets_count > 0 or cards_count > 0
                    })
                except Exception as e:
                    logger.warning(f"Failed to get counts for language {lang}: {e}")
                    continue
            
            return {
                "languages": languages_info,
                "total": len(languages_info)
            }
            
    except Exception as e:
        logger.error(f"Failed to fetch languages: {e}")
        return {"languages": [], "total": 0}


@router.get("/cards")
async def get_pokedata_cards(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    set_id: Optional[str] = Query(None),
    lang: str = Query('en', description="Language code (en, fr, de, es, it, ja, etc.)")
):
    """Get cards from pokedata_cards_{lang} table"""
    try:
        # Validate language
        lang = validate_language(lang)
        table_name = f"pokedata_cards_{lang}"
        
        async with get_db_session() as db:
            # Build query
            where_clauses = []
            params = {"skip": skip, "limit": limit}
            
            if search:
                where_clauses.append("name ILIKE :search")
                params["search"] = f"%{search}%"
            
            if set_id:
                where_clauses.append("set_id = :set_id")
                params["set_id"] = set_id
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get total count
            count_query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {where_sql}")
            count_result = await db.execute(count_query, params)
            total = count_result.scalar()
            
            # Get cards
            query = text(f"""
                SELECT 
                    id, tcgdex_id, local_id, name, set_id, set_name, 
                    category, rarity, illustrator, hp, types, stage, 
                    evolves_from, retreat_cost, image_url, 
                    set_release_date, created_at
                FROM {table_name}
                WHERE {where_sql}
                ORDER BY id
                LIMIT :limit OFFSET :skip
            """)
            
            result = await db.execute(query, params)
            cards = []
            for row in result:
                # Fix image URL to include proper extension
                image_url = row.image_url
                if image_url and not image_url.endswith(('.jpg', '.png', '.webp')):
                    image_url = f"{image_url}/high.webp"
                
                cards.append({
                    "id": row.id,
                    "tcgdex_id": row.tcgdex_id,
                    "local_id": row.local_id,
                    "name": row.name,
                    "set_id": row.set_id,
                    "set_name": row.set_name,
                    "category": row.category,
                    "rarity": row.rarity,
                    "illustrator": row.illustrator,
                    "hp": row.hp,
                    "types": row.types,
                    "stage": row.stage,
                    "evolves_from": row.evolves_from,
                    "retreat_cost": row.retreat_cost,
                    "image_url": image_url,
                    "set_release_date": str(row.set_release_date) if row.set_release_date else None,
                    "created_at": str(row.created_at) if row.created_at else None,
                    "language": lang
                })
            
            return {
                "data": cards,
                "total": total,
                "skip": skip,
                "limit": limit,
                "language": lang
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch pokedata cards: {e}")
        return {"data": [], "total": 0, "skip": skip, "limit": limit, "language": lang}


@router.get("/sets")
async def get_pokedata_sets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    lang: str = Query('en', description="Language code (en, fr, de, es, it, ja, etc.)")
):
    """Get sets from pokedata_sets_{lang} table"""
    try:
        # Validate language
        lang = validate_language(lang)
        table_name = f"pokedata_sets_{lang}"
        
        async with get_db_session() as db:
            # Build query
            where_clauses = []
            params = {"skip": skip, "limit": limit}
            
            if search:
                where_clauses.append("name ILIKE :search")
                params["search"] = f"%{search}%"
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get total count
            count_query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {where_sql}")
            count_result = await db.execute(count_query, params)
            total = count_result.scalar()
            
            # Get sets
            query = text(f"""
                SELECT 
                    id, tcgdex_id, name, code, total_cards, 
                    release_date, symbol_url, logo_url, created_at
                FROM {table_name}
                WHERE {where_sql}
                ORDER BY id
                LIMIT :limit OFFSET :skip
            """)
            
            result = await db.execute(query, params)
            sets = []
            for row in result:
                # Fix image URLs to include proper extensions
                symbol_url = row.symbol_url
                if symbol_url and not symbol_url.endswith(('.jpg', '.png', '.webp', '.svg')):
                    symbol_url = f"{symbol_url}.png"
                
                logo_url = row.logo_url
                if logo_url and not logo_url.endswith(('.jpg', '.png', '.webp', '.svg')):
                    logo_url = f"{logo_url}.png"
                
                sets.append({
                    "id": row.id,
                    "tcgdex_id": row.tcgdex_id,
                    "name": row.name,
                    "code": row.code,
                    "total_cards": row.total_cards,
                    "release_date": str(row.release_date) if row.release_date else None,
                    "symbol_url": symbol_url,
                    "logo_url": logo_url,
                    "created_at": str(row.created_at) if row.created_at else None,
                    "language": lang
                })
            
            return {
                "data": sets,
                "total": total,
                "skip": skip,
                "limit": limit,
                "language": lang
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch pokedata sets: {e}")
        return {"data": [], "total": 0, "skip": skip, "limit": limit, "language": lang}


@router.get("/sets/{set_id}/cards")
async def get_set_cards(
    set_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    lang: str = Query('en', description="Language code (en, fr, de, es, it, ja, etc.)")
):
    """Get all cards in a specific set"""
    try:
        # Validate language
        lang = validate_language(lang)
        table_name = f"pokedata_cards_{lang}"
        
        async with get_db_session() as db:
            params = {"set_id": set_id, "skip": skip, "limit": limit}
            
            # Get total count
            count_query = text(f"SELECT COUNT(*) FROM {table_name} WHERE set_id = :set_id")
            count_result = await db.execute(count_query, params)
            total = count_result.scalar()
            
            # Get cards
            query = text(f"""
                SELECT 
                    id, tcgdex_id, local_id, name, set_id, set_name,
                    category, rarity, illustrator, hp, types, image_url
                FROM {table_name}
                WHERE set_id = :set_id
                ORDER BY local_id
                LIMIT :limit OFFSET :skip
            """)
            
            result = await db.execute(query, params)
            cards = []
            for row in result:
                # Fix image URL to include proper extension
                image_url = row.image_url
                if image_url and not image_url.endswith(('.jpg', '.png', '.webp')):
                    image_url = f"{image_url}/high.webp"
                
                cards.append({
                    "id": row.id,
                    "tcgdex_id": row.tcgdex_id,
                    "local_id": row.local_id,
                    "name": row.name,
                    "set_id": row.set_id,
                    "set_name": row.set_name,
                    "category": row.category,
                    "rarity": row.rarity,
                    "illustrator": row.illustrator,
                    "hp": row.hp,
                    "types": row.types,
                    "image_url": image_url,
                    "language": lang
                })
            
            return {
                "data": cards,
                "total": total,
                "skip": skip,
                "limit": limit,
                "language": lang
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch cards for set {set_id}: {e}")
        return {"data": [], "total": 0, "skip": skip, "limit": limit, "language": lang}


@router.get("/cards/{card_id}/details")
async def get_card_details(
    card_id: int,
    lang: str = Query('en', description="Language code (en, fr, de, es, it, ja, etc.)")
):
    """Get detailed information for a specific card"""
    try:
        # Validate language
        lang = validate_language(lang)
        table_name = f"pokedata_cards_{lang}"
        
        async with get_db_session() as db:
            # Get full card details - only query columns that exist
            query = text(f"""
                SELECT 
                    id, tcgdex_id, local_id, name, set_id, set_name,
                    category, rarity, illustrator,
                    hp, types, stage, evolves_from, retreat_cost, 
                    image_url, set_release_date, created_at
                FROM {table_name}
                WHERE id = :card_id
            """)
            
            result = await db.execute(query, {"card_id": card_id})
            row = result.first()
            
            if not row:
                raise HTTPException(status_code=404, detail=f"Card {card_id} not found")
            
            # Fix image URL
            image_url = row.image_url
            if image_url and not image_url.endswith(('.jpg', '.png', '.webp')):
                image_url = f"{image_url}/high.webp"
            
            card_detail = {
                "id": row.id,
                "tcgdex_id": row.tcgdex_id,
                "local_id": row.local_id,
                "name": row.name,
                "set_id": row.set_id,
                "set_name": row.set_name,
                "category": row.category or "",
                "rarity": row.rarity or "",
                "illustrator": row.illustrator or "",
                "hp": row.hp,
                "types": row.types or [],
                "stage": row.stage or "",
                "evolves_from": row.evolves_from or "",
                "retreat_cost": row.retreat_cost,
                "image_url": image_url,
                "set_release_date": str(row.set_release_date) if row.set_release_date else None,
                "created_at": str(row.created_at) if row.created_at else None,
                "language": lang,
                # Placeholder for future pricing data
                "pricing": {
                    "market_price": None,
                    "ebay_avg_price": None,
                    "ebay_listings": []
                }
            }
            
            return card_detail
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch card details for {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch card details: {str(e)}")
