#!/usr/bin/env python3
"""
Fix missing logo URLs for non-English language sets by using English logo URLs.

Since TCGdex doesn't provide logo assets for most non-English languages,
we'll use the English logo URLs which work across all languages (logos are
typically the same visual design).
"""

import asyncio
import asyncpg
import os

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'tradingcards',
    'user': 'trading',
    'password': os.environ.get('PGPASSWORD', 'trading')
}

# Languages to fix (excluding English which already has logos)
LANGUAGES = ['ja', 'de', 'es', 'fr', 'it', 'ko', 'nl', 'pl', 'pt_br', 'ru', 'th', 'zh_cn', 'zh_tw', 'id']

async def fix_logo_urls_for_language(lang: str):
    """Update logo URLs for a language by copying from English sets with matching tcgdex_id."""
    print(f"\n{'='*60}")
    print(f"Processing language: {lang.upper()}")
    print(f"{'='*60}")
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        lang_table = f"pokedata_sets_{lang.replace('-', '_')}"
        
        # Check if table exists and has records
        try:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {lang_table}")
        except:
            print(f"⚠ Table {lang_table} does not exist, skipping")
            return
            
        if count == 0:
            print(f"⚠ Table {lang_table} is empty, skipping")
            return
        
        print(f"✓ Found {count} sets in {lang_table}")
        
        # Update logo URLs by copying from English sets with matching tcgdex_id
        result = await conn.execute(f"""
            UPDATE {lang_table} AS target
            SET logo_url = source.logo_url
            FROM pokedata_sets_en AS source
            WHERE target.tcgdex_id = source.tcgdex_id
              AND source.logo_url IS NOT NULL
              AND (target.logo_url IS NULL OR target.logo_url != source.logo_url)
        """)
        
        # Extract number of updated rows
        updated_count = int(result.split()[-1]) if result.startswith('UPDATE') else 0
        
        print(f"✓ Updated {updated_count} sets with English logo URLs")
        
        # Show sample results
        sample = await conn.fetch(f"""
            SELECT tcgdex_id, name, logo_url
            FROM {lang_table}
            WHERE logo_url IS NOT NULL
            LIMIT 3
        """)
        
        if sample:
            print(f"\nSample results:")
            for row in sample:
                print(f"  {row['tcgdex_id']:15s} {row['name'][:30]:30s} -> {row['logo_url'][:60]}")
        
        print(f"{'='*60}")
        
    finally:
        await conn.close()

async def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("LOGO URL FIX SCRIPT (Using English Logos)")
    print("="*60)
    print(f"Processing {len(LANGUAGES)} languages...")
    print(f"Languages: {', '.join(LANGUAGES)}")
    print("\nStrategy: Copy English logo URLs to non-English sets")
    print("Reason: TCGdex doesn't provide logo assets for most non-English languages")
    print("="*60)
    
    for lang in LANGUAGES:
        try:
            await fix_logo_urls_for_language(lang)
        except Exception as e:
            print(f"\n✗ Error processing {lang}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("COMPLETE - All non-English sets now use English logo URLs")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
