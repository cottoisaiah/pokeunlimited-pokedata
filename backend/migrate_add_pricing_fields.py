#!/usr/bin/env python3
"""
💰 Database Migration: Add Pricing Fields
Adds TCGPlayer and CardMarket pricing columns
"""

import asyncio
import asyncpg
import structlog

logger = structlog.get_logger()

# Database configuration
DATABASE_URL = "postgresql://trading:trading@localhost:5432/tradingcards"

# Supported languages
LANGUAGES = ['en', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'nl', 'pl', 'pt_br', 'ru', 'th', 'zh_cn', 'zh_tw', 'id']


async def migrate_table(conn: asyncpg.Connection, table_name: str) -> bool:
    """Add pricing fields to a single table"""
    try:
        logger.info(f"Migrating table: {table_name}")
        
        # Check if columns already exist
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = $1 
            AND column_name IN ('tcgplayer_prices', 'cardmarket_prices', 'pricing_last_updated')
        """
        existing_cols = await conn.fetch(check_query, table_name)
        existing_col_names = {row['column_name'] for row in existing_cols}
        
        # Add columns that don't exist
        columns_to_add = []
        
        if 'tcgplayer_prices' not in existing_col_names:
            columns_to_add.append("ADD COLUMN tcgplayer_prices JSONB DEFAULT NULL")
        
        if 'cardmarket_prices' not in existing_col_names:
            columns_to_add.append("ADD COLUMN cardmarket_prices JSONB DEFAULT NULL")
        
        if 'pricing_last_updated' not in existing_col_names:
            columns_to_add.append("ADD COLUMN pricing_last_updated TIMESTAMP DEFAULT NULL")
        
        if columns_to_add:
            alter_query = f"ALTER TABLE {table_name} {', '.join(columns_to_add)}"
            await conn.execute(alter_query)
            logger.info(f"Added {len(columns_to_add)} columns to {table_name}", columns=columns_to_add)
        else:
            logger.info(f"All pricing columns already exist in {table_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate {table_name}: {e}")
        return False


async def main():
    """Run migration for all language tables"""
    print("""
    💰 Database Migration: Pricing Fields
    =====================================
    
    Adding columns:
    - tcgplayer_prices JSONB - TCGPlayer pricing (normal, holofoil, reverseHolofoil, 1stEdition)
    - cardmarket_prices JSONB - CardMarket pricing (averageSellPrice, lowPrice, trendPrice, avg1, avg7, avg30)
    - pricing_last_updated TIMESTAMP - Last pricing update timestamp
    
    """)
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        success_count = 0
        fail_count = 0
        
        for lang in LANGUAGES:
            table_name = f"pokedata_cards_{lang}"
            
            try:
                success = await migrate_table(conn, table_name)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"Error migrating {table_name}: {e}")
                fail_count += 1
        
        print(f"""
    ✅ Migration Complete
    ====================
    Success: {success_count} tables
    Failed: {fail_count} tables
    Total: {len(LANGUAGES)} tables
        """)
        
    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(main())
