"""
OAuth-Enhanced eBay API Client
Integrates OAuth tokens for Shopping and Trading API access
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime, timezone
import json

try:
    from ebaysdk.finding import Connection as FindingConnection
    from ebaysdk.shopping import Connection as ShoppingConnection  
    from ebaysdk.trading import Connection as TradingConnection
    from ebaysdk.exception import ConnectionError as EbayConnectionError
    EBAY_SDK_AVAILABLE = True
except ImportError:
    EBAY_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

class OAuthEbayClient:
    """eBay API Client with OAuth token support"""
    
    def __init__(self):
        self.app_id = os.getenv('EBAY_APP_ID')
        self.dev_id = os.getenv('EBAY_DEV_ID')
        self.cert_id = os.getenv('EBAY_CERT_ID')
        self.sandbox = os.getenv('EBAY_SANDBOX', 'false').lower() == 'true'
        
        # OAuth token storage (in production, use database)
        self._oauth_tokens = {}
        
        # Initialize API connections
        self.finding_api = None
        self.shopping_api = None
        self.trading_api = None
        
        if EBAY_SDK_AVAILABLE:
            self._init_apis()
    
    def _init_apis(self):
        """Initialize API connections"""
        if self.app_id:
            # Finding API (App ID only)
            self.finding_api = FindingConnection(
                appid=self.app_id,
                config_file=None,
                siteid="EBAY-US",
                sandbox=self.sandbox,
                debug=False
            )
            
            # Shopping API (App ID + OAuth token when available)
            self.shopping_api = ShoppingConnection(
                appid=self.app_id,
                config_file=None,
                siteid="EBAY-US",
                sandbox=self.sandbox,
                debug=False
            )
            
            # Trading API (App ID + Dev ID + Cert ID + OAuth token)
            if self.dev_id and self.cert_id:
                self.trading_api = TradingConnection(
                    appid=self.app_id,
                    devid=self.dev_id,
                    certid=self.cert_id,
                    config_file=None,
                    siteid="EBAY-US",
                    sandbox=self.sandbox,
                    debug=False
                )
    
    def set_oauth_token(self, user_id: str, token_data: Dict[str, Any]):
        """Store OAuth token for a user"""
        self._oauth_tokens[user_id] = {
            'access_token': token_data.get('access_token'),
            'token_type': token_data.get('token_type', 'Bearer'),
            'expires_in': token_data.get('expires_in'),
            'refresh_token': token_data.get('refresh_token'),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"OAuth token stored for user {user_id}")
    
    def get_oauth_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get OAuth token for a user"""
        return self._oauth_tokens.get(user_id)
    
    def has_valid_oauth_token(self, user_id: str) -> bool:
        """Check if user has a valid OAuth token"""
        token_data = self.get_oauth_token(user_id)
        if not token_data:
            return False
        
        # TODO: Check token expiration
        return bool(token_data.get('access_token'))
    
    # Finding API methods (no OAuth required)
    def find_items_by_keywords(self, keywords: str, **kwargs) -> Dict[str, Any]:
        """Search for items using Finding API"""
        if not self.finding_api:
            raise RuntimeError("Finding API not initialized")
        
        params = {
            'keywords': keywords,
            'paginationInput': kwargs.get('pagination', {'entriesPerPage': 10}),
            **kwargs
        }
        
        try:
            response = self.finding_api.execute('findItemsByKeywords', params)
            return response.dict() if hasattr(response, 'dict') else {}
        except EbayConnectionError as e:
            logger.error(f"Finding API error: {e}")
            raise
    
    def find_completed_items(self, keywords: str, **kwargs) -> Dict[str, Any]:
        """Search for completed items using Finding API"""
        if not self.finding_api:
            raise RuntimeError("Finding API not initialized")
        
        params = {
            'keywords': keywords,
            'paginationInput': kwargs.get('pagination', {'entriesPerPage': 10}),
            **kwargs
        }
        
        try:
            response = self.finding_api.execute('findCompletedItems', params)
            return response.dict() if hasattr(response, 'dict') else {}
        except EbayConnectionError as e:
            logger.error(f"Finding API error: {e}")
            raise
    
    # Shopping API methods (OAuth required for most calls)
    def get_ebay_time(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get eBay official time using Shopping API"""
        if not self.shopping_api:
            raise RuntimeError("Shopping API not initialized")
        
        # Add OAuth token if available
        if user_id and self.has_valid_oauth_token(user_id):
            token_data = self.get_oauth_token(user_id)
            self.shopping_api.config.set('token', token_data['access_token'])
        
        try:
            response = self.shopping_api.execute('GeteBayTime', {})
            return response.dict() if hasattr(response, 'dict') else {}
        except EbayConnectionError as e:
            logger.error(f"Shopping API error: {e}")
            raise
    
    def get_item_details(self, item_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed item information using Shopping API"""
        if not self.shopping_api:
            raise RuntimeError("Shopping API not initialized")
        
        # OAuth token required for detailed item info
        if not user_id or not self.has_valid_oauth_token(user_id):
            raise RuntimeError("OAuth token required for Shopping API item details")
        
        token_data = self.get_oauth_token(user_id)
        self.shopping_api.config.set('token', token_data['access_token'])
        
        params = {'ItemID': item_id}
        
        try:
            response = self.shopping_api.execute('GetSingleItem', params)
            return response.dict() if hasattr(response, 'dict') else {}
        except EbayConnectionError as e:
            logger.error(f"Shopping API error: {e}")
            raise
    
    # Trading API methods (OAuth always required)
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information using Trading API"""
        if not self.trading_api:
            raise RuntimeError("Trading API not initialized")
        
        if not self.has_valid_oauth_token(user_id):
            raise RuntimeError("OAuth token required for Trading API")
        
        token_data = self.get_oauth_token(user_id)
        self.trading_api.config.set('token', token_data['access_token'])
        
        try:
            response = self.trading_api.execute('GetUser', {})
            return response.dict() if hasattr(response, 'dict') else {}
        except EbayConnectionError as e:
            logger.error(f"Trading API error: {e}")
            raise
    
    def get_my_ebay_selling(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Get user's selling information using Trading API"""
        if not self.trading_api:
            raise RuntimeError("Trading API not initialized")
        
        if not self.has_valid_oauth_token(user_id):
            raise RuntimeError("OAuth token required for Trading API")
        
        token_data = self.get_oauth_token(user_id)
        self.trading_api.config.set('token', token_data['access_token'])
        
        params = {
            'ActiveList': kwargs.get('active_list', {'Include': True}),
            'SoldList': kwargs.get('sold_list', {'Include': True}),
            **kwargs
        }
        
        try:
            response = self.trading_api.execute('GetMyeBaySelling', params)
            return response.dict() if hasattr(response, 'dict') else {}
        except EbayConnectionError as e:
            logger.error(f"Trading API error: {e}")
            raise
    
    # Utility methods
    def test_api_connectivity(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Test connectivity to all available APIs"""
        results = {
            'finding_api': {'available': False, 'working': False, 'error': None},
            'shopping_api': {'available': False, 'working': False, 'error': None, 'oauth_required': True},
            'trading_api': {'available': False, 'working': False, 'error': None, 'oauth_required': True},
            'oauth_status': {
                'has_token': bool(user_id and self.has_valid_oauth_token(user_id)),
                'user_id': user_id
            }
        }
        
        # Test Finding API
        if self.finding_api:
            results['finding_api']['available'] = True
            try:
                response = self.find_items_by_keywords('pokemon card', pagination={'entriesPerPage': 1})
                results['finding_api']['working'] = True
            except Exception as e:
                results['finding_api']['error'] = str(e)
        
        # Test Shopping API
        if self.shopping_api:
            results['shopping_api']['available'] = True
            try:
                response = self.get_ebay_time(user_id)
                results['shopping_api']['working'] = True
            except Exception as e:
                results['shopping_api']['error'] = str(e)
        
        # Test Trading API
        if self.trading_api:
            results['trading_api']['available'] = True
            if user_id and self.has_valid_oauth_token(user_id):
                try:
                    response = self.get_user_info(user_id)
                    results['trading_api']['working'] = True
                except Exception as e:
                    results['trading_api']['error'] = str(e)
            else:
                results['trading_api']['error'] = "OAuth token required"
        
        return results
    
    def get_api_capabilities(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get available API capabilities based on authentication status"""
        has_oauth = bool(user_id and self.has_valid_oauth_token(user_id))
        
        return {
            'finding_api': {
                'available': bool(self.finding_api),
                'capabilities': [
                    'Search active listings',
                    'Search completed items',
                    'Category browsing',
                    'Basic item information'
                ] if self.finding_api else []
            },
            'shopping_api': {
                'available': bool(self.shopping_api),
                'oauth_required': True,
                'oauth_available': has_oauth,
                'capabilities': [
                    'Detailed item information',
                    'Category information',
                    'eBay official time',
                    'Item status checks'
                ] if self.shopping_api and has_oauth else []
            },
            'trading_api': {
                'available': bool(self.trading_api),
                'oauth_required': True,
                'oauth_available': has_oauth,
                'capabilities': [
                    'User account information',
                    'Selling management',
                    'Bidding history',
                    'Account preferences'
                ] if self.trading_api and has_oauth else []
            }
        }

# Global instance
oauth_ebay_client = OAuthEbayClient()

# For backwards compatibility
def get_ebay_client() -> OAuthEbayClient:
    """Get the global eBay client instance"""
    return oauth_ebay_client
