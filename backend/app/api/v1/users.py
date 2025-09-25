"""
🎯 Users API
User management and profile endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
import structlog

from app.models.user_models import User
from app.core.security import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "subscription_tier": current_user.subscription_tier,
        "api_tier": current_user.api_tier,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }