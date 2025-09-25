"""
🎯 TCGPlayer API Service
Production-ready integration with TCGPlayer marketplace API
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.database import get_db_session
from app.models.product_models import Product, ProductPricing, PriceHistory
from app.services.cache_service import cache_service

logger = structlog.get_logger(__name__)

@dataclass
class TCGPlayerAuthResponse:
    """TCGPlayer authentication response"""
    access_token: str
    token_type: str
    expires_in: int
    user_name: str

@dataclass
class TCGPlayerProduct:
    """TCGPlayer product data structure"""
    product_id: int
    name: str
    group_name: str
    category_name: str
    number: str
    rarity: str
    image_url: str
    url: str
    clean_name: str

@dataclass
class TCGPlayerPricing:
    """TCGPlayer pricing data structure"""
    product_id: int
    low_price: Optional[float]
    mid_price: Optional[float]
    high_price: Optional[float]
    market_price: Optional[float]
    direct_low_price: Optional[float]
    sub_type_name: str

class TCGPlayerService:
    """Professional TCGPlayer API integration service"""
    
    def __init__(self):
        self.base_url = settings.TCGPLAYER_BASE_URL
        self.public_key = settings.TCGPLAYER_PUBLIC_KEY
        self.private_key = settings.TCGPLAYER_PRIVATE_KEY
        
        # Authentication
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # HTTP client with retry and timeout
        timeout = httpx.Timeout(settings.API_TIMEOUT)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(
                max_connections=settings.MAX_CONCURRENT_REQUESTS,
                max_keepalive_connections=20
            )
        )
        
        # Rate limiting
        self.last_request_time = 0
        self.request_delay = settings.REQUEST_DELAY_MS / 1000
        
        # Pokemon category ID
        self.pokemon_category_id = 3
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def _ensure_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated request with error handling"""
        await self._ensure_rate_limit()
        
        # Ensure authentication
        if not await self._is_authenticated():
            await self.authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "PokeUnlimited-PokeData/1.0"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            
            if response.status_code == 401:
                # Token expired, re-authenticate
                logger.warning("TCGPlayer token expired, re-authenticating")
                await self.authenticate()
                headers["Authorization"] = f"Bearer {self.access_token}"
                
                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs
                )
            
            if response.status_code == 429:
                # Rate limited
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"TCGPlayer rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return await self._make_request(method, endpoint, **kwargs)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "TCGPlayer API error",
                status_code=e.response.status_code,
                response=e.response.text,
                endpoint=endpoint
            )
            return None
        except Exception as e:
            logger.error("TCGPlayer request failed", error=str(e), endpoint=endpoint)
            return None
    
    async def authenticate(self) -> bool:
        """Authenticate with TCGPlayer API"""
        cache_key = "tcgplayer:auth_token"
        
        # Try to get cached token first
        cached_token = await cache_service.get(cache_key)
        if cached_token:
            auth_data = json.loads(cached_token)
            self.access_token = auth_data["access_token"]
            self.token_expires_at = datetime.fromisoformat(auth_data["expires_at"])
            
            if datetime.utcnow() < self.token_expires_at:
                logger.info("Using cached TCGPlayer authentication token")
                return True
        
        # Get new token
        logger.info("Authenticating with TCGPlayer API...")
        
        try:
            # First, get authorization code (this is simplified - in production you'd use OAuth flow)
            auth_url = f"{self.base_url}/token"
            
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.public_key,
                "client_secret": self.private_key
            }
            
            response = await self.client.post(
                auth_url,
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            self.token_expires_at = datetime.utcnow() + timedelta(
                seconds=token_data["expires_in"] - 60  # 60s buffer
            )
            
            # Cache the token
            cache_data = {
                "access_token": self.access_token,
                "expires_at": self.token_expires_at.isoformat()
            }
            
            await cache_service.set(
                cache_key,
                json.dumps(cache_data),
                ttl=token_data["expires_in"] - 120  # 2min buffer
            )
            
            logger.info("TCGPlayer authentication successful")
            return True
            
        except Exception as e:
            logger.error("TCGPlayer authentication failed", error=str(e))
            return False
    
    async def _is_authenticated(self) -> bool:
        """Check if current token is valid"""
        if not self.access_token or not self.token_expires_at:
            return False
        
        return datetime.utcnow() < self.token_expires_at
    
    async def search_pokemon_products(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[TCGPlayerProduct]:
        """Search Pokemon products in TCGPlayer catalog"""
        cache_key = f"tcgplayer:search:{query}:{limit}:{offset}"
        
        # Try cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            data = json.loads(cached_result)
            return [TCGPlayerProduct(**item) for item in data]
        
        # Build search parameters
        params = {
            "q": query,
            "limit": min(limit, 250),  # TCGPlayer max
            "offset": offset,
            "sortBy": "relevance",
            "productTypes": "Cards"
        }
        
        # Add filters if provided
        if filters:
            params.update(filters)
        
        endpoint = f"/catalog/categories/{self.pokemon_category_id}/search"
        
        response = await self._make_request("GET", endpoint, params=params)
        
        if not response or not response.get("success"):
            return []
        
        products = []
        for item in response.get("results", []):
            product = TCGPlayerProduct(
                product_id=item.get("productId"),
                name=item.get("name", ""),
                group_name=item.get("groupName", ""),
                category_name=item.get("categoryName", ""),
                number=item.get("number", ""),
                rarity=item.get("rarity", ""),
                image_url=item.get("imageUrl", ""),
                url=item.get("url", ""),
                clean_name=item.get("cleanName", item.get("name", ""))
            )
            products.append(product)
        
        # Cache results
        cache_data = [
            {
                "product_id": p.product_id,
                "name": p.name,
                "group_name": p.group_name,
                "category_name": p.category_name,
                "number": p.number,
                "rarity": p.rarity,
                "image_url": p.image_url,
                "url": p.url,
                "clean_name": p.clean_name
            }
            for p in products
        ]
        
        await cache_service.set(
            cache_key,
            json.dumps(cache_data),
            ttl=settings.CACHE_TTL_DEFAULT
        )
        
        logger.info(f"Found {len(products)} Pokemon products for query: {query}")
        return products
    
    async def get_product_pricing(
        self, 
        product_ids: List[int]
    ) -> List[TCGPlayerPricing]:
        """Get current market pricing for multiple products"""
        if not product_ids:
            return []
        
        # Split into batches of 250 (TCGPlayer limit)
        batch_size = 250
        all_pricing = []
        
        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i + batch_size]
            batch_pricing = await self._get_pricing_batch(batch)
            all_pricing.extend(batch_pricing)
        
        return all_pricing
    
    async def _get_pricing_batch(self, product_ids: List[int]) -> List[TCGPlayerPricing]:
        """Get pricing for a batch of products"""
        product_ids_str = ",".join(map(str, product_ids))
        cache_key = f"tcgplayer:pricing:{hash(product_ids_str)}"
        
        # Try cache first (short TTL for pricing)
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            data = json.loads(cached_result)
            return [TCGPlayerPricing(**item) for item in data]
        
        endpoint = f"/pricing/marketprices/{product_ids_str}"
        
        response = await self._make_request("GET", endpoint)
        
        if not response or not response.get("success"):
            return []
        
        pricing_data = []
        for item in response.get("results", []):
            pricing = TCGPlayerPricing(
                product_id=item.get("productId"),
                low_price=item.get("lowPrice"),
                mid_price=item.get("midPrice"),
                high_price=item.get("highPrice"),
                market_price=item.get("marketPrice"),
                direct_low_price=item.get("directLowPrice"),
                sub_type_name=item.get("subTypeName", "Normal")
            )
            pricing_data.append(pricing)
        
        # Cache with short TTL for pricing data
        cache_data = [
            {
                "product_id": p.product_id,
                "low_price": p.low_price,
                "mid_price": p.mid_price,
                "high_price": p.high_price,
                "market_price": p.market_price,
                "direct_low_price": p.direct_low_price,
                "sub_type_name": p.sub_type_name
            }
            for p in pricing_data
        ]
        
        await cache_service.set(
            cache_key,
            json.dumps(cache_data),
            ttl=settings.CACHE_TTL_PRICING
        )
        
        logger.info(f"Retrieved pricing for {len(pricing_data)} products")
        return pricing_data
    
    async def get_product_details(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed product information"""
        cache_key = f"tcgplayer:product:{product_id}"
        
        # Try cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        endpoint = f"/catalog/products/{product_id}"
        
        response = await self._make_request("GET", endpoint)
        
        if not response or not response.get("success"):
            return None
        
        product_data = response.get("results", [])
        if not product_data:
            return None
        
        product = product_data[0]
        
        # Cache with longer TTL for product details
        await cache_service.set(
            cache_key,
            json.dumps(product),
            ttl=settings.CACHE_TTL_ANALYTICS
        )
        
        return product
    
    async def sync_product_catalog(self, max_products: int = 1000) -> int:
        """Sync Pokemon products from TCGPlayer to local database"""
        logger.info(f"Starting TCGPlayer catalog sync (max {max_products} products)")
        
        synced_count = 0
        offset = 0
        batch_size = 250
        
        async with get_db_session() as db:
            while synced_count < max_products:
                # Search for products
                products = await self.search_pokemon_products(
                    query="pokemon",
                    limit=batch_size,
                    offset=offset
                )
                
                if not products:
                    break
                
                # Process each product
                for tcg_product in products:
                    if synced_count >= max_products:
                        break
                    
                    # Check if product exists
                    existing = await db.execute(
                        select(Product).where(
                            Product.tcgplayer_id == tcg_product.product_id
                        )
                    )
                    existing_product = existing.scalar_one_or_none()
                    
                    if not existing_product:
                        # Create new product
                        new_product = Product(
                            name=tcg_product.name,
                            set_name=tcg_product.group_name,
                            rarity=tcg_product.rarity,
                            number=tcg_product.number,
                            product_type="Cards",
                            image_url=tcg_product.image_url,
                            tcgplayer_id=tcg_product.product_id,
                            is_active=True,
                            is_tracked=True
                        )
                        
                        db.add(new_product)
                        synced_count += 1
                        
                        logger.debug(f"Added new product: {tcg_product.name}")
                
                await db.commit()
                offset += batch_size
                
                # Respect rate limits
                await asyncio.sleep(1)
        
        logger.info(f"TCGPlayer catalog sync complete: {synced_count} products")
        return synced_count
    
    async def update_pricing_data(self, max_products: int = 500) -> int:
        """Update pricing data for tracked products"""
        logger.info(f"Starting TCGPlayer pricing update (max {max_products} products)")
        
        async with get_db_session() as db:
            # Get products that need pricing updates
            query = (
                select(Product)
                .where(
                    Product.is_tracked == True,
                    Product.tcgplayer_id.isnot(None)
                )
                .order_by(Product.last_price_update.asc().nullsfirst())
                .limit(max_products)
            )
            
            result = await db.execute(query)
            products = result.scalars().all()
            
            if not products:
                logger.info("No products need pricing updates")
                return 0
            
            # Get TCGPlayer IDs
            tcgplayer_ids = [p.tcgplayer_id for p in products if p.tcgplayer_id]
            
            # Get pricing data
            pricing_data = await self.get_product_pricing(tcgplayer_ids)
            pricing_dict = {p.product_id: p for p in pricing_data}
            
            updated_count = 0
            
            for product in products:
                if product.tcgplayer_id not in pricing_dict:
                    continue
                
                pricing = pricing_dict[product.tcgplayer_id]
                
                # Update or create pricing record
                pricing_query = await db.execute(
                    select(ProductPricing).where(
                        ProductPricing.product_id == product.id
                    )
                )
                pricing_record = pricing_query.scalar_one_or_none()
                
                if not pricing_record:
                    pricing_record = ProductPricing(product_id=product.id)
                    db.add(pricing_record)
                
                # Update pricing data
                pricing_record.tcgplayer_market_price = pricing.market_price
                pricing_record.tcgplayer_low_price = pricing.low_price
                pricing_record.tcgplayer_mid_price = pricing.mid_price
                pricing_record.tcgplayer_high_price = pricing.high_price
                pricing_record.tcgplayer_direct_low = pricing.direct_low_price
                pricing_record.tcgplayer_last_updated = datetime.utcnow()
                
                # Update unified market price (simple average for now)
                if pricing.market_price:
                    pricing_record.market_price = pricing.market_price
                    pricing_record.confidence_score = 0.95  # High confidence for TCGPlayer
                
                # Update product timestamp
                product.last_price_update = datetime.utcnow()
                
                # Create price history record
                history_record = PriceHistory(
                    product_id=product.id,
                    source="tcgplayer",
                    price_type="market",
                    price=pricing.market_price or 0,
                    timestamp=datetime.utcnow()
                )
                db.add(history_record)
                
                updated_count += 1
            
            await db.commit()
            
            logger.info(f"TCGPlayer pricing update complete: {updated_count} products")
            return updated_count

# Global service instance
tcgplayer_service = TCGPlayerService()