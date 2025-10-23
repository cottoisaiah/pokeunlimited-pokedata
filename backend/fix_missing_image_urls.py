#!/usr/bin/env python3
"""
Quick fix script to populate missing image URLs for cards that have been enriched but are missing images.
This fetches image URLs from TCGdex API for cards that have category but no image_url.
"""

import asyncio
import asyncpg
import httpx
import os

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'tradingcards',
    'user': 'trading',
    'password': os.environ.get('PGPASSWORD', 'trading')
}

# Languages to process
LANGUAGES = ['ja', 'de', 'es', 'fr', 'it', 'ko', 'nl', 'pl', 'pt_br', 'ru', 'th', 'zh_cn', 'zh_tw', 'id']

async def populate_missing_images(lang: str):
    """Populate missing image URLs for enriched cards."""
    print(f"\n{'='*60}")
    print(f"Processing language: {lang.upper()}")
    print(f"{'='*60}")
    
    conn = await asyncpg.connect(**DB_CONFIG)
    table_name = f"pokedata_cards_{lang.replace('-', '_')}"
    
    try:
        # Find cards that have been enriched (have category) but missing image_url
        cards = await conn.fetch(f"""
            SELECT id, tcgdex_id, name
            FROM {table_name}
            WHERE category IS NOT NULL 
              AND category != ''
              AND (image_url IS NULL OR image_url = '')
            LIMIT 1000
        """)
        
        if not cards:
            print(f"✓ No cards with missing images found")
            return
        
        print(f"Found {len(cards)} cards with missing images")
        
        updated = 0
        async with httpx.AsyncClient(timeout=10.0) as client:
            for card in cards:
                try:
                    # Fetch card from TCGdex
                    url = f"https://api.tcgdex.net/v2/{lang}/cards/{card['tcgdex_id']}"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        image_url = data.get('image', '')
                        
                        if image_url:
                            await conn.execute(
                                f"UPDATE {table_name} SET image_url = $1 WHERE id = $2",
                                image_url, card['id']
                            )
                            updated += 1
                            print(f"  ✓ {card['tcgdex_id']:20s} {card['name'][:30]:30s}")
                    
                    # Rate limiting
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    print(f"  ✗ Error for {card['tcgdex_id']}: {e}")
        
        print(f"\n{'='*60}")
        print(f"Language {lang.upper()} Summary: Updated {updated}/{len(cards)} cards")
        print(f"{'='*60}")
        
    finally:
        await conn.close()

async def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("MISSING IMAGE URL FIX SCRIPT")
    print("="*60)
    print("Populating image URLs for enriched cards...")
    
    for lang in LANGUAGES:
        try:
            await populate_missing_images(lang)
        except Exception as e:
            print(f"\n✗ Error processing {lang}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
