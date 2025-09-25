"""
eBay API Configuration and Management Service
"""

import os
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
import redis
import json
import logging

from app.models.browse_api_models import EbayApiUsage
from app.models.database import get_db_session

logger = logging.getLogger(__name__)

class EbayApiConfig:
    """eBay API Configuration Manager"""
    
    def __init__(self):
        # eBay API Credentials
        self.client_id = os.getenv('EBAY_CLIENT_ID')
        self.client_secret = os.getenv('EBAY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('EBAY_REDIRECT_URI', 'https://your-domain.com/auth/ebay/callback')
        
        # API Endpoints
        self.sandbox_mode = os.getenv('EBAY_SANDBOX', 'false').lower() == 'true'
        self.base_url = self._get_base_url()
        
        # Rate Limiting
        self.daily_rate_limit = int(os.getenv('EBAY_DAILY_RATE_LIMIT', '5000'))
        self.requests_per_second = int(os.getenv('EBAY_REQUESTS_PER_SECOND', '5'))
        
        # Redis for caching and rate limiting
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Authentication tokens cache keys
        self.access_token_key = 'ebay:access_token'
        self.refresh_token_key = 'ebay:refresh_token'
        self.token_expires_key = 'ebay:token_expires'
        
        # Rate limiting keys
        self.rate_limit_key = f'ebay:rate_limit:{date.today().isoformat()}'
        self.error_count_key = f'ebay:errors:{date.today().isoformat()}'
    
    def _get_base_url(self) -> str:
        """Get the appropriate eBay API base URL"""
        if self.sandbox_mode:
            return 'https://api.sandbox.ebay.com'
        return 'https://api.ebay.com'
    
    @property
    def is_configured(self) -> bool:
        """Check if eBay API is properly configured"""
        return bool(self.client_id and self.client_secret)
    
    def get_oauth_url(self, scopes: List[str] = None) -> str:
        """Generate OAuth authorization URL"""
        if not scopes:
            scopes = ['https://api.ebay.com/oauth/api_scope/buy.shopping.search']
        
        scope_string = ' '.join(scopes)
        auth_url = f"{self.base_url}/identity/v1/oauth2/authorize"
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': scope_string,
            'state': 'your_state_value'  # Should be randomly generated in production
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_url}?{query_string}"
    
    async def get_access_token(self) -> Optional[str]:
        """Get cached access token or refresh if needed"""
        try:
            # Check if we have a valid cached token
            token = self.redis_client.get(self.access_token_key)
            expires_str = self.redis_client.get(self.token_expires_key)
            
            if token and expires_str:
                expires_at = datetime.fromisoformat(expires_str)
                if datetime.utcnow() < expires_at - timedelta(minutes=5):  # 5 min buffer
                    return token
            
            # Token expired or doesn't exist, need to refresh
            refresh_token = self.redis_client.get(self.refresh_token_key)
            if refresh_token:
                return await self._refresh_access_token(refresh_token)
            
            logger.warning("No valid access token or refresh token available")
            return None
            
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None
    
    async def _refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh the access token using refresh token"""
        # This would implement the actual OAuth refresh flow
        # For now, return None to indicate token refresh is needed
        logger.info("Token refresh needed - implement OAuth flow")
        return None
    
    def cache_tokens(self, access_token: str, refresh_token: str, expires_in: int):
        """Cache authentication tokens"""
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        self.redis_client.setex(self.access_token_key, expires_in, access_token)
        self.redis_client.set(self.refresh_token_key, refresh_token)
        self.redis_client.set(self.token_expires_key, expires_at.isoformat())
    
    async def check_rate_limit(self) -> Dict[str, any]:
        """Check current rate limit status"""
        try:
            # Get current usage from Redis
            current_calls = int(self.redis_client.get(self.rate_limit_key) or 0)
            current_errors = int(self.redis_client.get(self.error_count_key) or 0)
            
            # Get database usage for today
            with get_db_session() as db:
                db_usage = db.query(EbayApiUsage).filter(
                    EbayApiUsage.date == date.today(),
                    EbayApiUsage.api_type == 'browse'
                ).first()
                
                if db_usage:
                    # Sync Redis with database
                    if db_usage.calls_made != current_calls:
                        self.redis_client.set(self.rate_limit_key, db_usage.calls_made)
                        current_calls = db_usage.calls_made
                    
                    if db_usage.errors_count != current_errors:
                        self.redis_client.set(self.error_count_key, db_usage.errors_count)
                        current_errors = db_usage.errors_count
            
            remaining_calls = max(0, self.daily_rate_limit - current_calls)
            usage_percentage = (current_calls / self.daily_rate_limit) * 100
            
            return {
                'calls_made': current_calls,
                'calls_remaining': remaining_calls,
                'daily_limit': self.daily_rate_limit,
                'usage_percentage': round(usage_percentage, 2),
                'errors_today': current_errors,
                'rate_limited': remaining_calls == 0
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return {
                'calls_made': 0,
                'calls_remaining': self.daily_rate_limit,
                'daily_limit': self.daily_rate_limit,
                'usage_percentage': 0,
                'errors_today': 0,
                'rate_limited': False
            }
    
    async def increment_api_usage(self, success: bool = True):
        """Increment API usage counters"""
        try:
            # Increment Redis counters
            self.redis_client.incr(self.rate_limit_key)
            self.redis_client.expire(self.rate_limit_key, 86400)  # Expire at end of day
            
            if not success:
                self.redis_client.incr(self.error_count_key)
                self.redis_client.expire(self.error_count_key, 86400)
            
            # Update database
            with get_db_session() as db:
                usage = db.query(EbayApiUsage).filter(
                    EbayApiUsage.date == date.today(),
                    EbayApiUsage.api_type == 'browse'
                ).first()
                
                if not usage:
                    usage = EbayApiUsage(
                        date=date.today(),
                        api_type='browse',
                        calls_limit=self.daily_rate_limit
                    )
                    db.add(usage)
                
                usage.calls_made = (usage.calls_made or 0) + 1
                if not success:
                    usage.errors_count = (usage.errors_count or 0) + 1
                
                usage.updated_at = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            logger.error(f"Error incrementing API usage: {str(e)}")
    
    async def get_usage_analytics(self, days: int = 30) -> Dict[str, any]:
        """Get API usage analytics for the past N days"""
        try:
            start_date = date.today() - timedelta(days=days)
            
            with get_db_session() as db:
                usage_data = db.query(EbayApiUsage).filter(
                    EbayApiUsage.date >= start_date,
                    EbayApiUsage.api_type == 'browse'
                ).order_by(EbayApiUsage.date.desc()).all()
                
                # Calculate analytics
                total_calls = sum(u.calls_made for u in usage_data)
                total_errors = sum(u.errors_count for u in usage_data)
                total_rate_hits = sum(u.rate_limit_hits for u in usage_data)
                
                avg_daily_calls = total_calls / len(usage_data) if usage_data else 0
                error_rate = (total_errors / total_calls * 100) if total_calls > 0 else 0
                
                daily_usage = []
                for usage in usage_data:
                    daily_usage.append({
                        'date': usage.date.isoformat(),
                        'calls_made': usage.calls_made,
                        'errors': usage.errors_count,
                        'usage_percentage': round((usage.calls_made / usage.calls_limit * 100), 2)
                    })
                
                return {
                    'period_days': days,
                    'total_calls': total_calls,
                    'total_errors': total_errors,
                    'total_rate_hits': total_rate_hits,
                    'avg_daily_calls': round(avg_daily_calls, 2),
                    'error_rate_percentage': round(error_rate, 2),
                    'daily_usage': daily_usage
                }
                
        except Exception as e:
            logger.error(f"Error getting usage analytics: {str(e)}")
            return {}

# Global configuration instance - lazy loaded
_ebay_config = None

def get_ebay_config() -> EbayApiConfig:
    """Get the global eBay configuration instance (lazy loading)"""
    global _ebay_config
    if _ebay_config is None:
        _ebay_config = EbayApiConfig()
    return _ebay_config

# For backward compatibility
ebay_config = get_ebay_config()

class RateLimitManager:
    """Rate limiting manager for eBay API calls"""
    
    def __init__(self, config: EbayApiConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.requests_per_second)
        self.last_request_time = 0
    
    async def acquire(self) -> bool:
        """Acquire rate limit token"""
        # Check daily limit first
        rate_status = await self.config.check_rate_limit()
        if rate_status['rate_limited']:
            logger.warning("Daily rate limit exceeded")
            return False
        
        # Acquire semaphore for per-second limiting
        await self.semaphore.acquire()
        
        # Ensure minimum time between requests
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.config.requests_per_second
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
        return True
    
    def release(self):
        """Release rate limit token"""
        self.semaphore.release()

# Global rate limiter
rate_limiter = RateLimitManager(ebay_config)
