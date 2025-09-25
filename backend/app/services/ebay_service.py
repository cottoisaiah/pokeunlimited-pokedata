"""
🎯 Enhanced eBay API Service
Production-ready integration with eBay Browse and Finding APIs
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.parse import quote

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
class eBayListing:
    """eBay listing data structure"""
    item_id: str
    title: str
    price: Optional[float]
    condition: str
    listing_type: str
    location: str
    shipping_cost: Optional[float]
    image_url: str
    item_url: str
    seller_username: str
    seller_feedback_score: int
    watchers: Optional[int]
    sold_quantity: Optional[int]
    end_time: Optional[datetime]

@dataclass
class eBaySearchResult:
    """eBay search result with analytics"""
    listings: List[eBayListing]
    total_count: int
    average_price: Optional[float]
    price_range: Tuple[Optional[float], Optional[float]]
    condition_breakdown: Dict[str, int]
    search_query: str

class EnhancedeBayService:
    """Professional eBay API integration with advanced analytics"""
    
    def __init__(self):
        self.app_id = settings.EBAY_APP_ID
        self.dev_id = settings.EBAY_DEV_ID  
        self.cert_id = settings.EBAY_CERT_ID
        self.client_id = settings.EBAY_CLIENT_ID
        self.client_secret = settings.EBAY_CLIENT_SECRET
        self.user_token = settings.EBAY_USER_TOKEN
        self.sandbox = settings.EBAY_SANDBOX
        
        # API endpoints - use production URLs
        if not self.sandbox:
            self.browse_api_url = "https://api.ebay.com/buy/browse/v1"
            self.finding_api_url = "https://svcs.ebay.com/services/search/FindingService/v1"
            self.oauth_api_url = "https://api.ebay.com/identity/v1/oauth2/token"
        else:
            self.browse_api_url = "https://api.sandbox.ebay.com/buy/browse/v1"
            self.finding_api_url = "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"
            self.oauth_api_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        
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
        self.pokemon_category_id = "2536"  # Trading Card Games
        
        # OAuth token management
        self.access_token = None
        self.token_expires_at = None
    
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
        """Ensure we don't exceed eBay rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _get_oauth_token(self) -> Optional[str]:
        """Get OAuth access token using client credentials"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope/buy.item.browse"
        }
        
        auth = (self.client_id, self.client_secret)
        
        try:
            response = await self.client.post(
                self.oauth_api_url,
                headers=headers,
                data=data,
                auth=auth
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 7200)  # Default 2 hours
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                
                logger.info("Successfully obtained eBay OAuth token")
                return self.access_token
            else:
                logger.error(f"Failed to get eBay OAuth token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting eBay OAuth token: {str(e)}")
            return None
    
    async def _make_browse_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make request to eBay Browse API"""
        await self._ensure_rate_limit()
        
        # Get OAuth token
        token = await self._get_oauth_token()
        if not token:
            logger.error("Could not obtain eBay OAuth token")
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Content-Type": "application/json"
        }
        
        url = f"{self.browse_api_url}{endpoint}"
        
        try:
            response = await self.client.get(url, headers=headers, params=params)
            
            if response.status_code == 429:
                # Rate limited
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"eBay Browse API rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return await self._make_browse_request(endpoint, params)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "eBay Browse API error",
                status_code=e.response.status_code,
                response=e.response.text[:500],
                endpoint=endpoint
            )
            return None
        except Exception as e:
            logger.error("eBay Browse request failed", error=str(e), endpoint=endpoint)
            return None
    
    async def _make_finding_request(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make request to eBay Finding API"""
        await self._ensure_rate_limit()
        
        # Build request parameters
        request_params = {
            "OPERATION-NAME": operation,
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self.app_id,
            "GLOBAL-ID": "EBAY-US",
            "RESPONSE-DATA-FORMAT": "JSON",
            **params
        }
        
        try:
            response = await self.client.get(
                self.finding_api_url,
                params=request_params
            )
            
            if response.status_code == 429:
                # Rate limited
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"eBay Finding API rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return await self._make_finding_request(operation, params)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "eBay Finding API error",
                status_code=e.response.status_code,
                response=e.response.text[:500],
                operation=operation
            )
            return None
        except Exception as e:
            logger.error("eBay Finding request failed", error=str(e), operation=operation)
            return None
    
    def _parse_finding_listing(self, item: Dict[str, Any]) -> eBayListing:
        """Parse eBay Finding API listing item"""
        # Extract price
        price = None
        current_price = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0]
        if current_price:
            price = float(current_price.get("__value__", 0))
        
        # Extract shipping cost
        shipping_cost = None
        shipping_info = item.get("shippingInfo", [{}])[0]
        if shipping_info and shipping_info.get("shippingServiceCost"):
            shipping_cost_data = shipping_info["shippingServiceCost"][0]
            shipping_cost = float(shipping_cost_data.get("__value__", 0))
        
        # Extract end time
        end_time = None
        if item.get("listingInfo", [{}])[0].get("endTime"):
            end_time_str = item["listingInfo"][0]["endTime"][0]
            end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
        
        # Extract seller info
        seller_info = item.get("sellerInfo", [{}])[0]
        seller_username = seller_info.get("sellerUserName", [""])[0]
        seller_feedback = int(seller_info.get("feedbackScore", [0])[0])
        
        return eBayListing(
            item_id=item.get("itemId", [""])[0],
            title=item.get("title", [""])[0],
            price=price,
            condition=item.get("condition", [{}])[0].get("conditionDisplayName", [""])[0],
            listing_type=item.get("listingInfo", [{}])[0].get("listingType", [""])[0],
            location=item.get("location", [""])[0],
            shipping_cost=shipping_cost,
            image_url=item.get("galleryURL", [""])[0],
            item_url=item.get("viewItemURL", [""])[0],
            seller_username=seller_username,
            seller_feedback_score=seller_feedback,
            watchers=None,  # Not available in Finding API
            sold_quantity=None,  # Not available in Finding API
            end_time=end_time
        )
    
    def _parse_browse_listing(self, item: Dict[str, Any]) -> eBayListing:
        """Parse eBay Browse API listing item"""
        # Extract price
        price = None
        if item.get("price"):
            price = float(item["price"]["value"])
        
        # Extract shipping cost
        shipping_cost = None
        shipping_options = item.get("shippingOptions", [])
        if shipping_options:
            shipping_cost_data = shipping_options[0].get("shippingCost")
            if shipping_cost_data:
                shipping_cost = float(shipping_cost_data["value"])
        
        # Extract seller info
        seller = item.get("seller", {})
        
        return eBayListing(
            item_id=item.get("itemId", ""),
            title=item.get("title", ""),
            price=price,
            condition=item.get("condition", ""),
            listing_type=item.get("buyingOptions", [""])[0] if item.get("buyingOptions") else "",
            location=item.get("itemLocation", {}).get("country", ""),
            shipping_cost=shipping_cost,
            image_url=item.get("image", {}).get("imageUrl", ""),
            item_url=item.get("itemWebUrl", ""),
            seller_username=seller.get("username", ""),
            seller_feedback_score=int(seller.get("feedbackScore", 0)),
            watchers=item.get("watchCount"),
            sold_quantity=item.get("quantitySold"),
            end_time=None  # Not always available in Browse API
        )
    
    async def search_pokemon_cards(
        self,
        query: str,
        limit: int = 50,
        condition: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort_order: str = "BestMatch"
    ) -> eBaySearchResult:
        """Enhanced Pokemon card search with analytics"""
        cache_key = f"ebay:search:{query}:{limit}:{condition}:{price_min}:{price_max}:{sort_order}"
        
        # Try cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            data = json.loads(cached_result)
            listings = [eBayListing(**item) for item in data["listings"]]
            return eBaySearchResult(
                listings=listings,
                total_count=data["total_count"],
                average_price=data["average_price"],
                price_range=tuple(data["price_range"]),
                condition_breakdown=data["condition_breakdown"],
                search_query=query
            )
        
        # Build search parameters
        search_query = f"pokemon {query}"
        params = {
            "keywords": search_query,
            "categoryId": self.pokemon_category_id,
            "paginationInput.entriesPerPage": min(limit, 100),
            "sortOrder": sort_order,
            "outputSelector": ["SellerInfo", "StoreInfo", "PictureURLLarge"]
        }
        
        # Add filters
        item_filters = []
        filter_index = 0
        
        if condition:
            item_filters.append({
                f"itemFilter({filter_index}).name": "Condition",
                f"itemFilter({filter_index}).value": condition
            })
            filter_index += 1
        
        if price_min is not None:
            item_filters.append({
                f"itemFilter({filter_index}).name": "MinPrice",
                f"itemFilter({filter_index}).value": str(price_min)
            })
            filter_index += 1
        
        if price_max is not None:
            item_filters.append({
                f"itemFilter({filter_index}).name": "MaxPrice",
                f"itemFilter({filter_index}).value": str(price_max)
            })
            filter_index += 1
        
        # Add filters to params
        for filter_dict in item_filters:
            params.update(filter_dict)
        
        # Make API request
        response = await self._make_finding_request("findItemsByKeywords", params)
        
        if not response:
            return eBaySearchResult([], 0, None, (None, None), {}, query)
        
        # Parse response
        search_result = response.get("findItemsByKeywordsResponse", [{}])[0]
        search_results = search_result.get("searchResult", [{}])[0]
        
        items = search_results.get("item", [])
        total_count = int(search_result.get("paginationOutput", [{}])[0].get("totalEntries", [0])[0])
        
        # Parse listings
        listings = []
        prices = []
        condition_counts = {}
        
        for item in items:
            try:
                listing = self._parse_finding_listing(item)
                listings.append(listing)
                
                if listing.price:
                    prices.append(listing.price)
                
                # Count conditions
                condition = listing.condition or "Unknown"
                condition_counts[condition] = condition_counts.get(condition, 0) + 1
                
            except Exception as e:
                logger.warning(f"Failed to parse eBay listing: {e}")
                continue
        
        # Calculate analytics
        average_price = sum(prices) / len(prices) if prices else None
        price_range = (min(prices), max(prices)) if prices else (None, None)
        
        # Create result
        result = eBaySearchResult(
            listings=listings,
            total_count=total_count,
            average_price=average_price,
            price_range=price_range,
            condition_breakdown=condition_counts,
            search_query=query
        )
        
        # Cache results
        cache_data = {
            "listings": [
                {
                    "item_id": l.item_id,
                    "title": l.title,
                    "price": l.price,
                    "condition": l.condition,
                    "listing_type": l.listing_type,
                    "location": l.location,
                    "shipping_cost": l.shipping_cost,
                    "image_url": l.image_url,
                    "item_url": l.item_url,
                    "seller_username": l.seller_username,
                    "seller_feedback_score": l.seller_feedback_score,
                    "watchers": l.watchers,
                    "sold_quantity": l.sold_quantity,
                    "end_time": l.end_time.isoformat() if l.end_time else None
                }
                for l in listings
            ],
            "total_count": total_count,
            "average_price": average_price,
            "price_range": list(price_range),
            "condition_breakdown": condition_counts
        }
        
        await cache_service.set(
            cache_key,
            json.dumps(cache_data),
            ttl=settings.CACHE_TTL_DEFAULT
        )
        
        logger.info(f"eBay search complete: {len(listings)} listings for '{query}'")
        return result
    
    async def get_sold_listings(
        self,
        query: str,
        limit: int = 50,
        days_back: int = 30
    ) -> List[eBayListing]:
        """Get recently sold listings for price analysis"""
        cache_key = f"ebay:sold:{query}:{limit}:{days_back}"
        
        # Try cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            data = json.loads(cached_result)
            return [eBayListing(**item) for item in data]
        
        # Build search parameters for sold listings
        search_query = f"pokemon {query}"
        params = {
            "keywords": search_query,
            "categoryId": self.pokemon_category_id,
            "paginationInput.entriesPerPage": min(limit, 100),
            "sortOrder": "EndTimeSoonest",
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "outputSelector": ["SellerInfo", "StoreInfo", "PictureURLLarge"]
        }
        
        # Make API request
        response = await self._make_finding_request("findCompletedItems", params)
        
        if not response:
            return []
        
        # Parse response
        search_result = response.get("findCompletedItemsResponse", [{}])[0]
        search_results = search_result.get("searchResult", [{}])[0]
        
        items = search_results.get("item", [])
        
        # Parse listings
        listings = []
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        for item in items:
            try:
                listing = self._parse_finding_listing(item)
                
                # Filter by date if end_time is available
                if listing.end_time and listing.end_time < cutoff_date:
                    continue
                
                listings.append(listing)
                
            except Exception as e:
                logger.warning(f"Failed to parse sold eBay listing: {e}")
                continue
        
        # Cache results
        cache_data = [
            {
                "item_id": l.item_id,
                "title": l.title,
                "price": l.price,
                "condition": l.condition,
                "listing_type": l.listing_type,
                "location": l.location,
                "shipping_cost": l.shipping_cost,
                "image_url": l.image_url,
                "item_url": l.item_url,
                "seller_username": l.seller_username,
                "seller_feedback_score": l.seller_feedback_score,
                "watchers": l.watchers,
                "sold_quantity": l.sold_quantity,
                "end_time": l.end_time.isoformat() if l.end_time else None
            }
            for l in listings
        ]
        
        await cache_service.set(
            cache_key,
            json.dumps(cache_data),
            ttl=settings.CACHE_TTL_ANALYTICS
        )
        
        logger.info(f"Found {len(listings)} sold listings for '{query}'")
        return listings
    
    async def get_market_insights(
        self,
        product_name: str,
        set_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive market insights for a Pokemon card"""
        # Build search query
        search_terms = [product_name]
        if set_name:
            search_terms.append(set_name)
        query = " ".join(search_terms)
        
        # Get current listings
        current_listings = await self.search_pokemon_cards(query, limit=100)
        
        # Get sold listings
        sold_listings = await self.get_sold_listings(query, limit=100)
        
        # Calculate insights
        insights = {
            "product_name": product_name,
            "set_name": set_name,
            "search_query": query,
            "timestamp": datetime.utcnow().isoformat(),
            
            # Current market data
            "current_listings": {
                "total_count": current_listings.total_count,
                "active_listings": len(current_listings.listings),
                "average_price": current_listings.average_price,
                "price_range": {
                    "min": current_listings.price_range[0],
                    "max": current_listings.price_range[1]
                },
                "condition_breakdown": current_listings.condition_breakdown
            },
            
            # Sold listings analysis
            "sold_analysis": self._analyze_sold_listings(sold_listings),
            
            # Price trends
            "price_trends": self._calculate_price_trends(current_listings, sold_listings),
            
            # Market health
            "market_health": self._assess_market_health(current_listings, sold_listings)
        }
        
        return insights
    
    def _analyze_sold_listings(self, sold_listings: List[eBayListing]) -> Dict[str, Any]:
        """Analyze sold listings for pricing insights"""
        if not sold_listings:
            return {"message": "No sold listings found"}
        
        prices = [l.price for l in sold_listings if l.price]
        
        if not prices:
            return {"message": "No pricing data available"}
        
        # Calculate statistics
        sorted_prices = sorted(prices)
        count = len(prices)
        
        return {
            "total_sold": len(sold_listings),
            "with_pricing": count,
            "average_price": sum(prices) / count,
            "median_price": sorted_prices[count // 2] if count % 2 == 1 else 
                          (sorted_prices[count // 2 - 1] + sorted_prices[count // 2]) / 2,
            "min_price": min(prices),
            "max_price": max(prices),
            "price_range": max(prices) - min(prices),
            "recent_sales_count": count
        }
    
    def _calculate_price_trends(
        self,
        current_listings: eBaySearchResult,
        sold_listings: List[eBayListing]
    ) -> Dict[str, Any]:
        """Calculate price trends and momentum"""
        sold_prices = [l.price for l in sold_listings if l.price]
        current_prices = [l.price for l in current_listings.listings if l.price]
        
        if not sold_prices or not current_prices:
            return {"message": "Insufficient data for trend analysis"}
        
        avg_sold = sum(sold_prices) / len(sold_prices)
        avg_current = sum(current_prices) / len(current_prices)
        
        # Calculate price momentum
        price_change = avg_current - avg_sold
        price_change_percent = (price_change / avg_sold) * 100 if avg_sold > 0 else 0
        
        # Determine trend
        if price_change_percent > 5:
            trend = "increasing"
        elif price_change_percent < -5:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "average_sold_price": avg_sold,
            "average_current_price": avg_current,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "trend": trend,
            "trend_strength": abs(price_change_percent)
        }
    
    def _assess_market_health(
        self,
        current_listings: eBaySearchResult,
        sold_listings: List[eBayListing]
    ) -> Dict[str, Any]:
        """Assess overall market health for the product"""
        # Calculate supply/demand indicators
        active_count = len(current_listings.listings)
        sold_count = len(sold_listings)
        
        # Supply/demand ratio
        supply_demand_ratio = active_count / sold_count if sold_count > 0 else float('inf')
        
        # Market liquidity assessment
        if supply_demand_ratio < 0.5:
            liquidity = "high"  # Low supply, high demand
        elif supply_demand_ratio < 2:
            liquidity = "moderate"
        else:
            liquidity = "low"  # High supply, low demand
        
        # Price volatility (coefficient of variation)
        current_prices = [l.price for l in current_listings.listings if l.price]
        price_volatility = 0
        if len(current_prices) > 1:
            mean_price = sum(current_prices) / len(current_prices)
            variance = sum((p - mean_price) ** 2 for p in current_prices) / len(current_prices)
            std_dev = variance ** 0.5
            price_volatility = (std_dev / mean_price) * 100 if mean_price > 0 else 0
        
        return {
            "active_listings": active_count,
            "recent_sales": sold_count,
            "supply_demand_ratio": supply_demand_ratio,
            "liquidity": liquidity,
            "price_volatility_percent": price_volatility,
            "market_activity": "active" if sold_count > 10 else "moderate" if sold_count > 5 else "low"
        }
    
    async def update_product_pricing(self, max_products: int = 300) -> int:
        """Update eBay pricing data for tracked products"""
        logger.info(f"Starting eBay pricing update (max {max_products} products)")
        
        async with get_db_session() as db:
            # Get products that need eBay pricing updates
            query = (
                select(Product)
                .where(Product.is_tracked == True)
                .order_by(Product.last_price_update.asc().nullsfirst())
                .limit(max_products)
            )
            
            result = await db.execute(query)
            products = result.scalars().all()
            
            if not products:
                logger.info("No products need eBay pricing updates")
                return 0
            
            updated_count = 0
            
            for product in products:
                try:
                    # Search for current listings
                    search_query = f"{product.name}"
                    if product.set_name:
                        search_query += f" {product.set_name}"
                    
                    current_listings = await self.search_pokemon_cards(
                        search_query,
                        limit=50
                    )
                    
                    if not current_listings.listings:
                        continue
                    
                    # Get or create pricing record
                    pricing_query = await db.execute(
                        select(ProductPricing).where(
                            ProductPricing.product_id == product.id
                        )
                    )
                    pricing_record = pricing_query.scalar_one_or_none()
                    
                    if not pricing_record:
                        pricing_record = ProductPricing(product_id=product.id)
                        db.add(pricing_record)
                    
                    # Update eBay pricing data
                    pricing_record.ebay_average_price = current_listings.average_price
                    if current_listings.price_range[0]:
                        pricing_record.ebay_low_price = current_listings.price_range[0]
                    if current_listings.price_range[1]:
                        pricing_record.ebay_high_price = current_listings.price_range[1]
                    pricing_record.ebay_listing_count = len(current_listings.listings)
                    pricing_record.ebay_last_updated = datetime.utcnow()
                    
                    # Update unified market price (combine with existing data)
                    if current_listings.average_price:
                        if pricing_record.tcgplayer_market_price:
                            # Average TCGPlayer and eBay prices
                            combined_price = (
                                pricing_record.tcgplayer_market_price + 
                                current_listings.average_price
                            ) / 2
                            pricing_record.market_price = combined_price
                            pricing_record.confidence_score = 0.85
                        else:
                            pricing_record.market_price = current_listings.average_price
                            pricing_record.confidence_score = 0.70  # Lower confidence for eBay only
                    
                    # Update product timestamp
                    product.last_price_update = datetime.utcnow()
                    
                    # Create price history record
                    if current_listings.average_price:
                        history_record = PriceHistory(
                            product_id=product.id,
                            source="ebay",
                            price_type="average",
                            price=current_listings.average_price,
                            timestamp=datetime.utcnow()
                        )
                        db.add(history_record)
                    
                    updated_count += 1
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Failed to update eBay pricing for {product.name}: {e}")
                    continue
            
            await db.commit()
            
            logger.info(f"eBay pricing update complete: {updated_count} products")
            return updated_count

# Global service instance
ebay_service = EnhancedeBayService()