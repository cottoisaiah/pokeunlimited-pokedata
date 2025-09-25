"""
🎯 TCGdx API Service
Production-ready integration with TCGdx API for Pokemon TCG data
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from tcgdexsdk import TCGdex, Language, Query

from app.core.config import settings

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import structlog
from tcgdexsdk import TCGdex, Language, Query

logger = structlog.get_logger(__name__)

@dataclass
class PokemonCard:
    """Pokemon card data structure from TCGdx"""
    id: str
    name: str
    image_url: str
    set_name: str
    set_id: str
    rarity: Optional[str]
    hp: Optional[int]
    types: List[str]
    tcgplayer_prices: Optional[Dict[str, float]]
    cardmarket_prices: Optional[Dict[str, float]]
    release_date: Optional[str]
    local_id: str
    variants: List[Dict[str, Any]]

@dataclass
class SetInfo:
    """Pokemon set information"""
    id: str
    name: str
    release_date: str
    card_count: int
    symbol_url: str
    logo_url: str

class TCGdexService:
    """Professional TCGdex API integration with caching and analytics"""
    
    def __init__(self):
        # Initialize TCGdx SDK
        self.sdk = TCGdex(Language.EN)
        
        # Cache for frequently accessed data
        self._card_cache = {}
        self._set_cache = {}
        self._cache_ttl = timedelta(hours=1)
        
        logger.info("TCGdx service initialized with English language support")
    
    def set_language(self, language: str = "en"):
        """Change the language for card data"""
        language_map = {
            "en": Language.EN,
            "fr": Language.FR,
            "de": Language.DE,
            "es": Language.ES,
            "it": Language.IT,
            "pt": Language.PT,
            "ja": Language.JA,
            "ko": Language.KO,
            "zh": Language.ZH,
            "ru": Language.RU
        }
        
        if language in language_map:
            self.sdk.setLanguage(language_map[language])
            logger.info(f"Language set to {language}")
        else:
            logger.warning(f"Unsupported language: {language}, keeping English")
    
    async def get_card(self, card_id: str) -> Optional[PokemonCard]:
        """Get detailed card information by ID"""
        try:
            # Check cache first
            if card_id in self._card_cache:
                cached_data, timestamp = self._card_cache[card_id]
                if datetime.now() - timestamp < self._cache_ttl:
                    return cached_data
            
            # Fetch from API
            card_data = await self.sdk.card.get(card_id)
            
            if not card_data:
                return None
            
            # Extract pricing data
            tcgplayer_prices = self._extract_tcgplayer_prices(card_data)
            cardmarket_prices = self._extract_cardmarket_prices(card_data)
            
            # Create card object
            pokemon_card = PokemonCard(
                id=card_data.id,
                name=card_data.name,
                image_url=card_data.get_image_url("high", "png") if hasattr(card_data, 'get_image_url') else "",
                set_name=card_data.set.name if hasattr(card_data, 'set') else "",
                set_id=card_data.set.id if hasattr(card_data, 'set') else "",
                rarity=card_data.rarity.name if hasattr(card_data, 'rarity') else None,
                hp=card_data.hp if hasattr(card_data, 'hp') else None,
                types=[t.name for t in card_data.types] if hasattr(card_data, 'types') else [],
                tcgplayer_prices=tcgplayer_prices,
                cardmarket_prices=cardmarket_prices,
                release_date=card_data.set.releaseDate if hasattr(card_data, 'set') else None,
                local_id=card_data.localId if hasattr(card_data, 'localId') else "",
                variants=self._extract_variants(card_data)
            )
            
            # Cache the result
            self._card_cache[card_id] = (pokemon_card, datetime.now())
            
            logger.info(f"Retrieved card: {pokemon_card.name} from set {pokemon_card.set_name}")
            return pokemon_card
            
        except Exception as e:
            logger.error(f"Error fetching card {card_id}: {str(e)}")
            return None
    
    async def search_cards(
        self, 
        query: str, 
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[PokemonCard]:
        """Search for Pokemon cards with advanced filtering"""
        try:
            # Build query
            search_query = Query()
            
            # Add name search
            search_query = search_query.contains("name", query)
            
            # Apply filters if provided
            if filters:
                if "set" in filters:
                    search_query = search_query.equal("set.id", filters["set"])
                
                if "rarity" in filters:
                    search_query = search_query.equal("rarity.name", filters["rarity"])
                
                if "type" in filters:
                    search_query = search_query.contains("types.name", filters["type"])
                
                if "min_hp" in filters:
                    search_query = search_query.greaterThan("hp", filters["min_hp"])
                
                if "max_hp" in filters:
                    search_query = search_query.lessThan("hp", filters["max_hp"])
            
            # Add pagination
            search_query = search_query.paginate(page=1, itemsPerPage=limit)
            
            # Execute search
            results = await self.sdk.card.list(search_query)
            
            # Convert to PokemonCard objects
            cards = []
            for card_data in results:
                try:
                    pokemon_card = await self._convert_to_pokemon_card(card_data)
                    if pokemon_card:
                        cards.append(pokemon_card)
                except Exception as e:
                    logger.warning(f"Error converting card {getattr(card_data, 'id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Found {len(cards)} cards for query: {query}")
            return cards
            
        except Exception as e:
            logger.error(f"Error searching cards: {str(e)}")
            return []
    
    async def get_set_info(self, set_id: str) -> Optional[SetInfo]:
        """Get Pokemon set information"""
        try:
            # Check cache
            if set_id in self._set_cache:
                cached_data, timestamp = self._set_cache[set_id]
                if datetime.now() - timestamp < self._cache_ttl:
                    return cached_data
            
            # Fetch from API
            set_data = await self.sdk.set.get(set_id)
            
            if not set_data:
                return None
            
            set_info = SetInfo(
                id=set_data.id,
                name=set_data.name,
                release_date=set_data.releaseDate if hasattr(set_data, 'releaseDate') else "",
                card_count=set_data.cardCount.total if hasattr(set_data, 'cardCount') else 0,
                symbol_url=set_data.get_symbol_url("png") if hasattr(set_data, 'get_symbol_url') else "",
                logo_url=set_data.get_logo_url("png") if hasattr(set_data, 'get_logo_url') else ""
            )
            
            # Cache the result
            self._set_cache[set_id] = (set_info, datetime.now())
            
            logger.info(f"Retrieved set info: {set_info.name}")
            return set_info
            
        except Exception as e:
            logger.error(f"Error fetching set {set_id}: {str(e)}")
            return None
    
    async def get_market_analysis(self, card_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive market analysis for a card"""
        try:
            card = await self.get_card(card_id)
            if not card:
                return None
            
            analysis = {
                "card_info": {
                    "name": card.name,
                    "set": card.set_name,
                    "rarity": card.rarity,
                    "types": card.types
                },
                "pricing": {
                    "tcgplayer": card.tcgplayer_prices or {},
                    "cardmarket": card.cardmarket_prices or {}
                },
                "market_insights": {
                    "has_pricing_data": bool(card.tcgplayer_prices or card.cardmarket_prices),
                    "variant_count": len(card.variants),
                    "collectibility_score": self._calculate_collectibility_score(card)
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting market analysis for {card_id}: {str(e)}")
            return None
    
    async def _convert_to_pokemon_card(self, card_data) -> Optional[PokemonCard]:
        """Convert TCGdx card data to PokemonCard object"""
        try:
            return PokemonCard(
                id=card_data.id,
                name=card_data.name,
                image_url=card_data.get_image_url("high", "png") if hasattr(card_data, 'get_image_url') else "",
                set_name=card_data.set.name if hasattr(card_data, 'set') else "",
                set_id=card_data.set.id if hasattr(card_data, 'set') else "",
                rarity=card_data.rarity.name if hasattr(card_data, 'rarity') else None,
                hp=card_data.hp if hasattr(card_data, 'hp') else None,
                types=[t.name for t in card_data.types] if hasattr(card_data, 'types') else [],
                tcgplayer_prices=self._extract_tcgplayer_prices(card_data),
                cardmarket_prices=self._extract_cardmarket_prices(card_data),
                release_date=card_data.set.releaseDate if hasattr(card_data, 'set') else None,
                local_id=card_data.localId if hasattr(card_data, 'localId') else "",
                variants=self._extract_variants(card_data)
            )
        except Exception as e:
            logger.warning(f"Error converting card data: {str(e)}")
            return None
    
    def _extract_tcgplayer_prices(self, card_data) -> Optional[Dict[str, float]]:
        """Extract TCGPlayer pricing data from card"""
        try:
            if hasattr(card_data, 'tcgplayer') and card_data.tcgplayer:
                prices = {}
                if hasattr(card_data.tcgplayer, 'prices'):
                    for price_type, price_data in card_data.tcgplayer.prices.items():
                        if hasattr(price_data, 'market'):
                            prices[price_type] = price_data.market
                return prices if prices else None
        except Exception as e:
            logger.debug(f"No TCGPlayer pricing data available: {str(e)}")
        return None
    
    def _extract_cardmarket_prices(self, card_data) -> Optional[Dict[str, float]]:
        """Extract Cardmarket pricing data from card"""
        try:
            if hasattr(card_data, 'cardmarket') and card_data.cardmarket:
                prices = {}
                if hasattr(card_data.cardmarket, 'prices'):
                    for price_type, price_value in card_data.cardmarket.prices.items():
                        prices[price_type] = price_value
                return prices if prices else None
        except Exception as e:
            logger.debug(f"No Cardmarket pricing data available: {str(e)}")
        return None
    
    def _extract_variants(self, card_data) -> List[Dict[str, Any]]:
        """Extract card variant information"""
        try:
            variants = []
            if hasattr(card_data, 'variants'):
                for variant in card_data.variants:
                    variants.append({
                        "name": variant.name if hasattr(variant, 'name') else "",
                        "finish": variant.finish if hasattr(variant, 'finish') else ""
                    })
            return variants
        except Exception as e:
            logger.debug(f"No variant data available: {str(e)}")
            return []
    
    def _calculate_collectibility_score(self, card: PokemonCard) -> float:
        """Calculate a collectibility score based on card attributes"""
        score = 0.0
        
        # Rarity bonus
        rarity_scores = {
            "Common": 1.0,
            "Uncommon": 2.0,
            "Rare": 3.0,
            "Rare Holo": 4.0,
            "Ultra Rare": 5.0,
            "Secret Rare": 6.0
        }
        score += rarity_scores.get(card.rarity, 1.0)
        
        # Pricing data availability
        if card.tcgplayer_prices:
            score += 2.0
        if card.cardmarket_prices:
            score += 1.0
        
        # Variant count
        score += len(card.variants) * 0.5
        
        # Normalize to 0-10 scale
        return min(score, 10.0)

# Global service instance
tcgdex_service = TCGdexService()

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from urllib.parse import quote

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.database import get_db_session
from app.models.product_models import Product, ProductPricing, PriceHistory

logger = structlog.get_logger(__name__)

class Language(Enum):
    """Supported languages for TCGdx API"""
    ENGLISH = "en"
    FRENCH = "fr" 
    SPANISH = "es"
    GERMAN = "de"
    ITALIAN = "it"
    JAPANESE = "ja"
    PORTUGUESE = "pt"
    KOREAN = "ko"
    CHINESE_SIMPLIFIED = "zh-cn"
    CHINESE_TRADITIONAL = "zh-tw"

@dataclass
class TCGdexCard:
    """TCGdex card data structure with embedded pricing"""
    id: str
    name: str
    image: str
    category: str
    set_id: str
    set_name: str
    rarity: str
    hp: Optional[int] = None
    types: List[str] = None
    pricing: Dict = None
    attacks: List[Dict] = None
    abilities: List[Dict] = None
    evolves_from: Optional[str] = None
    national_pokedex_number: Optional[int] = None

@dataclass
class TCGdexSet:
    """TCGdex set information"""
    id: str
    name: str
    symbol: str
    release_date: str
    card_count: int
    image: str
    series: str

@dataclass
class PricingData:
    """Comprehensive pricing data from TCGdx"""
    tcgplayer_normal: Optional[Dict] = None
    tcgplayer_holofoil: Optional[Dict] = None
    tcgplayer_reverse_holo: Optional[Dict] = None
    tcgplayer_first_edition: Optional[Dict] = None
    cardmarket_normal: Optional[Dict] = None
    cardmarket_foil: Optional[Dict] = None
    last_updated: Optional[datetime] = None

class TCGdexClient:
    """Professional TCGdex API client with caching and rate limiting"""
    
    def __init__(self, language: Language = Language.ENGLISH):
        self.language = language.value
        self.base_url = "https://api.tcgdx.net/v2"
        self.graphql_url = "https://api.tcgdx.net/graphql"
        
        # HTTP client with optimized settings
        timeout = httpx.Timeout(30.0)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            ),
            headers={
                "User-Agent": "PokeData-Platform/1.0 (https://poketrade.redexct.xyz)",
                "Accept": "application/json"
            }
        )
        
        # Rate limiting
        self.last_request_time = 0
        self.request_delay = 0.1  # TCGdx is generous with rate limits
        
        # Cache for reducing API calls
        self.card_cache = {}
        self.set_cache = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def _ensure_rate_limit(self):
        """Respectful rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        await self._ensure_rate_limit()
        
        url = f"{self.base_url}/{self.language}{endpoint}"
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"TCGdx API request successful", endpoint=endpoint, status=response.status_code)
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "TCGdx API error",
                status_code=e.response.status_code,
                response=e.response.text[:500],
                endpoint=endpoint
            )
            return None
        except Exception as e:
            logger.error("TCGdx request failed", error=str(e), endpoint=endpoint)
            return None
    
    async def get_card(self, card_id: str) -> Optional[TCGdexCard]:
        """Get detailed card information including pricing"""
        # Check cache first
        if card_id in self.card_cache:
            return self.card_cache[card_id]
        
        data = await self._make_request(f"/cards/{card_id}")
        if not data:
            return None
        
        card = self._parse_card(data)
        self.card_cache[card_id] = card
        return card
    
    async def search_cards(
        self,
        name: Optional[str] = None,
        set_id: Optional[str] = None,
        types: Optional[List[str]] = None,
        rarity: Optional[str] = None,
        hp_min: Optional[int] = None,
        hp_max: Optional[int] = None,
        page: int = 1,
        limit: int = 100
    ) -> List[TCGdexCard]:
        """Advanced card search with multiple filters"""
        params = {"page": page, "pageSize": min(limit, 250)}  # TCGdx max page size
        
        if name:
            params["q"] = name
        if set_id:
            params["set"] = set_id
        if types:
            params["types"] = ",".join(types)
        if rarity:
            params["rarity"] = rarity
        if hp_min:
            params["hp-gte"] = hp_min
        if hp_max:
            params["hp-lte"] = hp_max
        
        data = await self._make_request("/cards", params)
        if not data or "data" not in data:
            return []
        
        cards = [self._parse_card(card_data) for card_data in data["data"]]
        
        # Cache the results
        for card in cards:
            self.card_cache[card.id] = card
        
        logger.info(f"TCGdx search returned {len(cards)} cards", query=name, set_id=set_id)
        return cards
    
    async def get_sets(self) -> List[TCGdexSet]:
        """Get all available Pokemon TCG sets"""
        if self.set_cache:
            return list(self.set_cache.values())
        
        data = await self._make_request("/sets")
        if not data or "data" not in data:
            return []
        
        sets = [self._parse_set(set_data) for set_data in data["data"]]
        
        # Cache sets
        for set_info in sets:
            self.set_cache[set_info.id] = set_info
        
        logger.info(f"TCGdx returned {len(sets)} sets")
        return sets
    
    async def get_set(self, set_id: str) -> Optional[TCGdexSet]:
        """Get specific set information"""
        if set_id in self.set_cache:
            return self.set_cache[set_id]
        
        data = await self._make_request(f"/sets/{set_id}")
        if not data:
            return None
        
        set_info = self._parse_set(data)
        self.set_cache[set_id] = set_info
        return set_info
    
    async def search_cards_graphql(self, query_variables: Dict) -> List[TCGdexCard]:
        """Advanced GraphQL search for complex queries"""
        graphql_query = """
        query SearchCards($name: String, $setId: String, $types: [String], $rarity: String) {
            cards(name: $name, set: $setId, types: $types, rarity: $rarity) {
                id
                name
                image
                category
                rarity
                hp
                types
                set {
                    id
                    name
                    symbol
                    releaseDate
                }
                attacks {
                    name
                    cost
                    damage
                    text
                }
                abilities {
                    name
                    type
                    text
                }
                pricing {
                    tcgplayer {
                        normal {
                            lowPrice
                            midPrice
                            highPrice
                            marketPrice
                            directLowPrice
                        }
                        holofoil {
                            lowPrice
                            midPrice
                            highPrice
                            marketPrice
                            directLowPrice
                        }
                        reverseHolofoil {
                            lowPrice
                            midPrice
                            highPrice
                            marketPrice
                            directLowPrice
                        }
                    }
                    cardmarket {
                        avg
                        low
                        trend
                        avg1
                        avg7
                        avg30
                    }
                }
            }
        }
        """
        
        try:
            response = await self.client.post(
                self.graphql_url,
                json={
                    "query": graphql_query,
                    "variables": query_variables
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and "cards" in data["data"]:
                return [self._parse_card(card_data) for card_data in data["data"]["cards"]]
            
        except Exception as e:
            logger.error("GraphQL query failed", error=str(e))
        
        return []
    
    def _parse_card(self, data: Dict) -> TCGdexCard:
        """Parse API response into structured card object"""
        pricing = self._extract_pricing_data(data.get("pricing", {}))
        
        return TCGdexCard(
            id=data["id"],
            name=data["name"],
            image=data.get("image", ""),
            category=data.get("category", ""),
            set_id=data.get("set", {}).get("id", ""),
            set_name=data.get("set", {}).get("name", ""),
            rarity=data.get("rarity", ""),
            hp=data.get("hp"),
            types=data.get("types", []),
            pricing=pricing,
            attacks=data.get("attacks", []),
            abilities=data.get("abilities", []),
            evolves_from=data.get("evolvesFrom"),
            national_pokedex_number=data.get("nationalPokedexNumber")
        )
    
    def _parse_set(self, data: Dict) -> TCGdexSet:
        """Parse set data from API response"""
        return TCGdexSet(
            id=data["id"],
            name=data["name"],
            symbol=data.get("symbol", ""),
            release_date=data.get("releaseDate", ""),
            card_count=data.get("cardCount", 0),
            image=data.get("image", ""),
            series=data.get("series", "")
        )
    
    def _extract_pricing_data(self, pricing_data: Dict) -> PricingData:
        """Extract comprehensive pricing data from TCGdx response"""
        tcgplayer = pricing_data.get("tcgplayer", {})
        cardmarket = pricing_data.get("cardmarket", {})
        
        return PricingData(
            tcgplayer_normal=tcgplayer.get("normal"),
            tcgplayer_holofoil=tcgplayer.get("holofoil"),
            tcgplayer_reverse_holo=tcgplayer.get("reverseHolofoil"),
            tcgplayer_first_edition=tcgplayer.get("1stEdition"),
            cardmarket_normal=cardmarket,
            cardmarket_foil=cardmarket,  # TCGdx includes foil in main cardmarket object
            last_updated=datetime.now()
        )

class TCGdexPokemonService:
    """High-level service for Pokemon-specific operations"""
    
    def __init__(self, client: TCGdexClient):
        self.client = client
    
    async def search_pokemon_cards(
        self,
        query: str,
        limit: int = 50,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        condition: Optional[str] = None
    ) -> List[TCGdexCard]:
        """Search Pokemon cards with pricing filters"""
        cards = await self.client.search_cards(name=query, limit=limit)
        
        # Apply pricing filters
        if min_price or max_price:
            filtered_cards = []
            for card in cards:
                market_price = self._get_market_price(card)
                if market_price:
                    if min_price and market_price < min_price:
                        continue
                    if max_price and market_price > max_price:
                        continue
                filtered_cards.append(card)
            cards = filtered_cards
        
        return cards
    
    async def get_trending_cards(self, limit: int = 20) -> List[TCGdexCard]:
        """Get trending Pokemon cards based on pricing activity"""
        # Search for popular Pokemon
        popular_pokemon = ["Charizard", "Pikachu", "Mewtwo", "Lugia", "Rayquaza"]
        trending_cards = []
        
        for pokemon in popular_pokemon:
            cards = await self.client.search_cards(name=pokemon, limit=5)
            # Filter for cards with recent price data
            for card in cards:
                if self._has_recent_pricing(card):
                    trending_cards.append(card)
        
        # Sort by market price descending
        trending_cards.sort(
            key=lambda c: self._get_market_price(c) or 0,
            reverse=True
        )
        
        return trending_cards[:limit]
    
    async def analyze_card_value(self, card_id: str) -> Dict[str, Any]:
        """Comprehensive value analysis for a card"""
        card = await self.client.get_card(card_id)
        if not card:
            return {}
        
        pricing = card.pricing
        market_price = self._get_market_price(card)
        
        # Extract price ranges
        tcg_normal = pricing.tcgplayer_normal or {}
        low_price = tcg_normal.get("lowPrice", 0)
        high_price = tcg_normal.get("highPrice", 0)
        
        return {
            "card_id": card.id,
            "name": card.name,
            "set": card.set_name,
            "current_market_price": market_price,
            "price_range": {
                "low": low_price,
                "high": high_price,
                "spread": high_price - low_price if high_price and low_price else 0
            },
            "rarity": card.rarity,
            "condition_modifiers": self._get_condition_modifiers(card),
            "investment_score": self._calculate_investment_score(card),
            "last_updated": pricing.last_updated.isoformat() if pricing.last_updated else None
        }
    
    def _get_market_price(self, card: TCGdexCard) -> Optional[float]:
        """Get the best market price for a card"""
        if not card.pricing:
            return None
        
        # Prefer holofoil for special cards, normal otherwise
        if "Holo" in card.rarity or any(word in card.name for word in ["GX", "EX", "V", "VMAX"]):
            if card.pricing.tcgplayer_holofoil:
                return card.pricing.tcgplayer_holofoil.get("marketPrice")
        
        if card.pricing.tcgplayer_normal:
            return card.pricing.tcgplayer_normal.get("marketPrice")
        
        return None
    
    def _has_recent_pricing(self, card: TCGdexCard) -> bool:
        """Check if card has recent pricing data"""
        if not card.pricing or not card.pricing.last_updated:
            return False
        
        # Consider pricing recent if within last 7 days
        cutoff = datetime.now() - timedelta(days=7)
        return card.pricing.last_updated > cutoff
    
    def _get_condition_modifiers(self, card: TCGdexCard) -> Dict[str, float]:
        """Get pricing modifiers for different card conditions"""
        base_price = self._get_market_price(card) or 0
        
        return {
            "mint": base_price * 1.0,
            "near_mint": base_price * 0.95,
            "excellent": base_price * 0.85,
            "good": base_price * 0.70,
            "light_played": base_price * 0.60,
            "played": base_price * 0.45,
            "poor": base_price * 0.25
        }
    
    def _calculate_investment_score(self, card: TCGdexCard) -> float:
        """Calculate investment potential score (0-100)"""
        score = 50  # Base score
        
        # Rarity bonus
        rarity_scores = {
            "Common": 0,
            "Uncommon": 10,
            "Rare": 20,
            "Rare Holo": 30,
            "Ultra Rare": 40,
            "Secret Rare": 50
        }
        score += rarity_scores.get(card.rarity, 0)
        
        # Popular Pokemon bonus
        popular_names = ["Charizard", "Pikachu", "Mewtwo", "Lugia", "Rayquaza"]
        if any(name in card.name for name in popular_names):
            score += 15
        
        # Special card types bonus
        if any(word in card.name for word in ["GX", "EX", "V", "VMAX", "Prime", "Legend"]):
            score += 10
        
        # Price stability (based on price range)
        market_price = self._get_market_price(card) or 0
        if market_price > 50:  # High-value cards
            score += 15
        elif market_price > 10:  # Mid-value cards
            score += 5
        
        return min(score, 100)  # Cap at 100