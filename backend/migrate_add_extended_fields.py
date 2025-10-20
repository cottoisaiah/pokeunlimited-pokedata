#!/usr/bin/env python3
"""
🔧 Database Migration: Add Extended Card Fields
Adds abilities, attacks, weaknesses, resistances, and variants columns
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
    """Add extended fields to a single table"""
    try:
        logger.info(f"Migrating table: {table_name}")
        
        # Check if columns already exist
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = $1 
            AND column_name IN ('abilities', 'attacks', 'weaknesses', 'resistances', 'variants')
        """
        existing_cols = await conn.fetch(check_query, table_name)
        existing_col_names = {row['column_name'] for row in existing_cols}
        
        # Add columns that don't exist
        columns_to_add = []
        
        if 'abilities' not in existing_col_names:
            columns_to_add.append("ADD COLUMN abilities JSONB DEFAULT '[]'::jsonb")
        
        if 'attacks' not in existing_col_names:
            columns_to_add.append("ADD COLUMN attacks JSONB DEFAULT '[]'::jsonb")
        
        if 'weaknesses' not in existing_col_names:
            columns_to_add.append("ADD COLUMN weaknesses JSONB DEFAULT '[]'::jsonb")
        
        if 'resistances' not in existing_col_names:
            columns_to_add.append("ADD COLUMN resistances JSONB DEFAULT '[]'::jsonb")
        
        if 'variants' not in existing_col_names:
            columns_to_add.append("ADD COLUMN variants JSONB DEFAULT '[]'::jsonb")
        
        if columns_to_add:
            alter_query = f"ALTER TABLE {table_name} {', '.join(columns_to_add)}"
            await conn.execute(alter_query)
            logger.info(f"Added {len(columns_to_add)} columns to {table_name}", columns=columns_to_add)
        else:
            logger.info(f"All columns already exist in {table_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate {table_name}: {e}")
        return False


async def main():
    """Run migration for all language tables"""
    print("""
    🔧 Database Migration: Extended Card Fields
    ===========================================
    
    Adding columns:
    - abilities JSONB - Pokemon abilities/powers with effects
    - attacks JSONB - Attack names, costs, damage, effects
    - weaknesses JSONB - Weakness types and multipliers
    - resistances JSONB - Resistance types and values
    - variants JSONB - Card variants (holo, reverse, etc.)
    
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
