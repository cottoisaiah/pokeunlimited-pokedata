"""
🗄️ Enhanced Database Models
Comprehensive data models for Pokemon TCG market intelligence platform
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# Create database engines
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    future=True
)

sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql://"),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    future=True
)

# Session makers
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Base class for all models
Base = declarative_base()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with proper cleanup"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_db_session() -> Session:
    """Get synchronous database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

async def init_db():
    """Initialize database with all tables"""
    async with async_engine.begin() as conn:
        # Import all models to ensure they're registered
        from app.models import (
            user_models,
            product_models,
            analytics_models,
            portfolio_models,
            browse_api_models
        )
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

async def drop_db():
    """Drop all database tables (use with caution!)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def close_db():
    """Close database connections"""
    await async_engine.dispose()