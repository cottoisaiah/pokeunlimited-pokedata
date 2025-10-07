"""
🎯 TCGdex Data Fetcher Service

Fetches live Pokemon TCG data from TCGdex API and synchronizes with database
Uses the tcgdex-sdk for proper pricing data integration
IMPORTANT: Always spell as TCGdex (NOT TCGdx) - see TCGDEX_SPELLING_REFERENCE.md
"""
import httpx
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_
from app.models.database import get_db_session
from app.models.product_models import ProductSet, Product, ProductPricing
from app.core.config import settings

# Import TCGdex SDK for proper card pricing
try:
    from tcgdex import TCGdex
    HAS_TCGDEX_SDK = True
except ImportError:
    logger.warning("tcgdex-sdk not available, falling back to HTTP client")
    HAS_TCGDEX_SDK = False

logger = logging.getLogger(__name__)


class TCGdexDataFetcher:
    """Service for fetching and synchronizing TCGdex Pokemon TCG data with pricing"""
    
    def __init__(self):
        self.base_url = "https://api.tcgdex.net/v2"
        self.language = "en"
        self.client = None
        # Initialize TCGdex SDK if available
        if HAS_TCGDEX_SDK:
            self.tcgdex_sdk = TCGdex("en")
        else:
            self.tcgdex_sdk = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=10),
            headers={
                "User-Agent": "PokeData-Platform/1.0 (https://poketrade.redexct.xyz)",
                "Accept": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    def _format_image_url(self, base_url: str, image_type: str = "logo", quality: str = "high", extension: str = "webp") -> str:
        """Format TCGdex image URLs with proper extensions and quality"""
        if image_type in ["logo", "symbol"]:
            # For logos and symbols, just add the extension
            return f"{base_url}.{extension}"
        elif image_type == "card":
            # For cards, add quality and extension
            return f"{base_url}/{quality}.{extension}"
        return base_url
    
    async def fetch_all_sets(self) -> List[Dict[str, Any]]:
        """Fetch all available Pokemon TCG sets from TCGdex API"""
        try:
            if self.tcgdex_sdk:
                # Use SDK if available
                sets_data = await asyncio.to_thread(self.tcgdex_sdk.fetch, "sets")
                sets_data = sets_data if isinstance(sets_data, list) else []
            else:
                # Fallback to HTTP client
                response = await self.client.get(f"{self.base_url}/{self.language}/sets")
                response.raise_for_status()
                sets_data = response.json()
            
            # Format image URLs for logos and symbols
            for set_data in sets_data:
                if 'logo' in set_data and set_data['logo']:
                    set_data['logo'] = self._format_image_url(set_data['logo'], "logo", extension="webp")
                if 'symbol' in set_data and set_data['symbol']:
                    set_data['symbol'] = self._format_image_url(set_data['symbol'], "symbol", extension="webp")
            
            logger.info(f"Fetched {len(sets_data)} sets from TCGdex API")
            return sets_data
        except Exception as e:
            logger.error(f"Failed to fetch sets from TCGdex API: {str(e)}")
            return []
    
    async def fetch_set_details(self, set_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific set from TCGdex API"""
        try:
            if self.tcgdex_sdk:
                # Use SDK if available
                set_data = await asyncio.to_thread(self.tcgdex_sdk.fetch, "set", set_id)
            else:
                # Fallback to HTTP client
                response = await self.client.get(f"{self.base_url}/{self.language}/sets/{set_id}")
                response.raise_for_status()
                set_data = response.json()
            
            # Format image URLs for logos and symbols
            if 'logo' in set_data and set_data['logo']:
                set_data['logo'] = self._format_image_url(set_data['logo'], "logo", extension="webp")
            if 'symbol' in set_data and set_data['symbol']:
                set_data['symbol'] = self._format_image_url(set_data['symbol'], "symbol", extension="webp")
            
            logger.info(f"Fetched set details for {set_id} from TCGdex API")
            return set_data
        except Exception as e:
            logger.error(f"Failed to fetch set {set_id} from TCGdex API: {str(e)}")
            return None
    
    async def fetch_set_cards_with_pricing(self, set_id: str) -> List[Dict[str, Any]]:
        """Fetch all cards from a specific set with pricing data from TCGdex API"""
        try:
            if self.tcgdex_sdk:
                # Use SDK to fetch cards with pricing
                cards_data = await asyncio.to_thread(self.tcgdex_sdk.fetch, "cards", params={"set": set_id})
            else:
                # Fallback to HTTP client
                response = await self.client.get(f"{self.base_url}/{self.language}/cards", params={"set": set_id})
                response.raise_for_status()
                cards_data = response.json()
            
            # Format image URLs and add pricing data for cards
            for card in cards_data:
                if 'image' in card and card['image']:
                    card['image'] = self._format_image_url(card['image'], "card", quality="low", extension="webp")
                
                # Add pricing data - TCGdex SDK should provide this
                if self.tcgdex_sdk and 'tcgplayer' in card:
                    tcgplayer_data = card.get('tcgplayer', {})
                    if 'prices' in tcgplayer_data:
                        prices = tcgplayer_data['prices']
                        # Get market price or normal price
                        market_price = None
                        if 'holofoil' in prices and 'market' in prices['holofoil']:
                            market_price = prices['holofoil']['market']
                        elif 'normal' in prices and 'market' in prices['normal']:
                            market_price = prices['normal']['market']
                        elif 'reverseHolofoil' in prices and 'market' in prices['reverseHolofoil']:
                            market_price = prices['reverseHolofoil']['market']
                        
                        if market_price:
                            card['price'] = float(market_price)
                        else:
                            # Default price estimation based on rarity
                            card['price'] = self._estimate_card_price(card)
                else:
                    # Estimate price based on card rarity if no pricing data
                    card['price'] = self._estimate_card_price(card)
            
            logger.info(f"Fetched {len(cards_data)} cards for set {set_id} from TCGdex API with pricing")
            return cards_data
        except Exception as e:
            logger.error(f"Failed to fetch cards for set {set_id} from TCGdex API: {str(e)}")
            return []
    
    def _estimate_card_price(self, card: Dict[str, Any]) -> float:
        """Estimate card price based on rarity and other factors"""
        rarity = card.get('rarity', '').lower()
        
        # Basic price estimation based on rarity
        price_map = {
            'common': 0.25,
            'uncommon': 0.50,
            'rare': 2.00,
            'rare holo': 5.00,
            'ultra rare': 15.00,
            'secret rare': 25.00,
            'rainbow rare': 35.00,
            'gold rare': 30.00,
            'promo': 3.00,
        }
        
        # Check for special keywords that increase value
        name = card.get('name', '').lower()
        if any(keyword in name for keyword in ['charizard', 'pikachu', 'mew', 'lugia']):
            multiplier = 2.0
        elif 'ex' in name or 'gx' in name or 'v' in name:
            multiplier = 1.5
        else:
            multiplier = 1.0
        
        base_price = price_map.get(rarity, 1.00)
        return round(base_price * multiplier, 2)
    
    async def fetch_set_cards(self, set_id: str) -> List[Dict[str, Any]]:
        """Backward compatibility - calls fetch_set_cards_with_pricing"""
        return await self.fetch_set_cards_with_pricing(set_id)


# Global instance  
tcgdex_fetcher = TCGdexDataFetcher()


async def sync_tcgdex_data(limit: Optional[int] = None) -> int:
    """Convenience function to sync TCGdex data"""
    async with TCGdexDataFetcher() as fetcher:
        return await fetcher.sync_all_sets(limit=limit)


async def sync_single_set(set_id: str) -> bool:
    """Convenience function to sync a single set"""
    async with TCGdexDataFetcher() as fetcher:
        return await fetcher.sync_complete_set(set_id)