"""
🔐 Security & Authentication Module
JWT-based authentication with role-based access control and API tier management
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.config import settings
from app.models.database import get_db_session
from app.models.user_models import User, APIKey

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    scopes: List[str] = []
    api_tier: str = "free"

class UserInToken(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    api_tier: str
    scopes: List[str]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a new access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a new refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        scopes: List[str] = payload.get("scopes", [])
        api_tier: str = payload.get("api_tier", "free")
        
        if user_id is None:
            return None
            
        token_data = TokenData(
            user_id=user_id,
            username=username,
            scopes=scopes,
            api_tier=api_tier
        )
        
        return token_data
        
    except jwt.PyJWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInToken:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(credentials.credentials)
    
    if token_data is None:
        raise credentials_exception
    
    async with get_db_session() as db:
        user = await db.get(User, token_data.user_id)
        
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        return UserInToken(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            api_tier=user.api_tier,
            scopes=user.scopes or []
        )

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInToken]:
    """Get the current authenticated user, or None if not authenticated"""
    if not credentials:
        return None
    
    token_data = verify_token(credentials.credentials)
    
    if token_data is None:
        return None
    
    try:
        async with get_db_session() as db:
            user = await db.get(User, token_data.user_id)
            
            if user is None or not user.is_active:
                return None
            
            return UserInToken(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                api_tier=user.api_tier,
                scopes=user.scopes or []
            )
    except Exception:
        return None

async def get_api_key_user(api_key: str) -> Optional[UserInToken]:
    """Authenticate user via API key"""
    async with get_db_session() as db:
        api_key_obj = await db.execute(
            "SELECT * FROM api_keys WHERE key_hash = %s AND is_active = true",
            [get_password_hash(api_key)]
        )
        
        api_key_data = api_key_obj.fetchone()
        if not api_key_data:
            return None
        
        user = await db.get(User, api_key_data['user_id'])
        if not user or not user.is_active:
            return None
        
        return UserInToken(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            api_tier=user.api_tier,
            scopes=api_key_data['scopes'] or []
        )

def require_scopes(required_scopes: List[str]):
    """Decorator to require specific scopes for endpoint access"""
    def scope_checker(current_user: UserInToken = Depends(get_current_user)):
        user_scopes = set(current_user.scopes)
        required_scopes_set = set(required_scopes)
        
        if not required_scopes_set.issubset(user_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return scope_checker

def require_api_tier(min_tier: str):
    """Decorator to require minimum API tier for endpoint access"""
    tier_hierarchy = {
        "free": 0,
        "gold": 1,
        "platinum": 2
    }
    
    def tier_checker(current_user: UserInToken = Depends(get_current_user)):
        user_tier_level = tier_hierarchy.get(current_user.api_tier, 0)
        required_tier_level = tier_hierarchy.get(min_tier, 0)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_tier} tier or higher"
            )
        
        return current_user
    
    return tier_checker

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
        self.cache = {}
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit"""
        # Implementation would use Redis for distributed rate limiting
        # This is a simplified in-memory version
        current_time = datetime.utcnow()
        
        if key not in self.cache:
            self.cache[key] = []
        
        # Remove old requests outside the window
        self.cache[key] = [
            req_time for req_time in self.cache[key]
            if (current_time - req_time).total_seconds() < self.window
        ]
        
        # Check if under limit
        if len(self.cache[key]) >= self.requests:
            return False
        
        # Add current request
        self.cache[key].append(current_time)
        return True

# Rate limiters for different API tiers
rate_limiters = {
    "free": RateLimiter(settings.RATE_LIMIT_FREE_TIER, settings.RATE_LIMIT_WINDOW),
    "gold": RateLimiter(settings.RATE_LIMIT_GOLD_TIER, settings.RATE_LIMIT_WINDOW),
    "platinum": RateLimiter(settings.RATE_LIMIT_PLATINUM_TIER, settings.RATE_LIMIT_WINDOW),
}

async def check_rate_limit(current_user: UserInToken = Depends(get_current_user)):
    """Check rate limiting for the current user"""
    rate_limiter = rate_limiters.get(current_user.api_tier)
    
    if rate_limiter and not await rate_limiter.is_allowed(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return current_user