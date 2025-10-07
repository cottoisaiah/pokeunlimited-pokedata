"""
🎯 Main API Router
Central routing configuration for all API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
import structlog

from app.core.security import get_current_user, check_rate_limit
from app.models.user_models import User

# Import API routers
from app.api.v1.products import router as products_router
from app.api.v1.sets import router as sets_router, tcgdex_router
from app.api.v1.pricing import router as pricing_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.users import router as users_router
from app.api.v1.search import router as search_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.pokedata import router as pokedata_router

logger = structlog.get_logger(__name__)
security = HTTPBearer()

# Create main API router
api_router = APIRouter()

# Health check endpoint (no auth required)
@api_router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "PokeUnlimited PokeData API",
        "version": "1.0.0"
    }

# Public endpoints (no authentication required)
api_router.include_router(
    sets_router,
    prefix="/sets",
    tags=["Sets"]
)

api_router.include_router(
    tcgdex_router,
    tags=["TCGdex"]
)

api_router.include_router(
    products_router,
    prefix="/products",
    tags=["Products"]
)

api_router.include_router(
    search_router,
    prefix="/search",
    tags=["Search"]
)

# Direct PokeData table access (public, no auth)
api_router.include_router(
    pokedata_router,
    prefix="/pokedata",
    tags=["PokeData"]
)

# Protected endpoints (authentication required)
# @api_router.middleware("http")
# async def add_rate_limiting(request: Request, call_next):
#     """Add rate limiting to protected endpoints"""
#     # Skip rate limiting for health check and public endpoints
#     if request.url.path in ["/api/v1/health", "/api/v1/products", "/api/v1/search"]:
#         response = await call_next(request)
#         return response
#     
#     # Apply rate limiting
#     try:
#         await check_rate_limit(request)
#         response = await call_next(request)
#         return response
#     except HTTPException as e:
#         raise e

# Protected routers
api_router.include_router(
    pricing_router,
    prefix="/pricing",
    tags=["Pricing"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    analytics_router,
    prefix="/analytics", 
    tags=["Analytics"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    portfolio_router,
    prefix="/portfolio",
    tags=["Portfolio"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    alerts_router,
    prefix="/alerts",
    tags=["Alerts"],
    dependencies=[Depends(get_current_user)]
)