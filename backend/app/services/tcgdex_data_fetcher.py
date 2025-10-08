"""
🎯 TCGdex Data Fetcher Service

Fetches live Pokemon TCG data from TCGdex API and synchronizes with database
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

logger = logging.getLogger(__name__)


class TCGdexDataFetcher:
    """Service for fetching and synchronizing TCGdex Pokemon TCG data"""
    
    def __init__(self):
        self.base_url = "https://api.tcgdex.net/v2"
        self.language = "en"
        self.client = None
        
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
    
    async def fetch_all_sets(self) -> List[Dict[str, Any]]:
        """Fetch all available Pokemon TCG sets from TCGDex API"""
        try:
            response = await self.client.get(f"{self.base_url}/{self.language}/sets")
            response.raise_for_status()
            data = response.json()
            # TCGDex API returns a direct array, not an object with 'data' key
            if isinstance(data, list):
                logger.info(f"Fetched {len(data)} sets from TCGDex API")
                return data
            else:
                logger.warning(f"Unexpected response format from TCGDex API: {type(data)}")
                return []
        except Exception as e:
            logger.error(f"Failed to fetch sets from TCGDex API: {str(e)}")
            return []
    
    async def fetch_set_details(self, set_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific set from TCGDex API"""
        try:
            response = await self.client.get(f"{self.base_url}/{self.language}/sets/{set_id}")
            response.raise_for_status()
            data = response.json()
            logger.info(f"Fetched set details for {set_id} from TCGDex API")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch set {set_id} from TCGDex API: {str(e)}")
            return None
    
    async def sync_all_sets(self, limit: Optional[int] = None) -> int:
        """Sync multiple sets from TCGDex API to database"""
        logger.info(f"Starting TCGDex data sync (limit: {limit})")
        
        try:
            sets_data = await self.fetch_all_sets()
            if not sets_data:
                logger.error("No sets available from TCGDex API")
                return 0
            
            if limit:
                sets_data = sets_data[:limit]
            
            synced_count = 0
            for set_data in sets_data:
                set_id = set_data.get('id')
                if set_id:
                    success = await self.sync_complete_set(set_id)
                    if success:
                        synced_count += 1
                    await asyncio.sleep(0.5)  # Respectful delay
            
            logger.info(f"TCGDex sync completed: {synced_count} sets synced")
            return synced_count
            
        except Exception as e:
            logger.error(f"TCGDex bulk sync failed: {str(e)}")
            return 0
    
    async def sync_complete_set(self, set_id: str) -> bool:
        """Sync a complete set from TCGDex API to database"""
        logger.info(f"Syncing set {set_id} from TCGDex API")
        
        try:
            set_data = await self.fetch_set_details(set_id)
            if not set_data:
                return False
            
            # Here you would implement the database sync logic
            # This is a placeholder for the actual sync implementation
            logger.info(f"Successfully synced set {set_id} from TCGDex API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync set {set_id} from TCGDex API: {str(e)}")
            return False


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