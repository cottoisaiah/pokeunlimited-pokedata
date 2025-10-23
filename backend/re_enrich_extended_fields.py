#!/usr/bin/env python3
"""
🎴 Re-enrich Cards with Extended Fields (Phase 2)
Updates already enriched cards with abilities, attacks, weaknesses, resistances
"""

import asyncio
import asyncpg
import httpx
import structlog
from typing import Optional, Dict, Any
import json

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

DATABASE_URL = "postgresql://trading:trading@localhost:5432/tradingcards"
TCGDEX_BASE_URL = "https://api.tcgdex.net/v2"


async def re_enrich_extended_fields(lang: str = 'en', batch_size: int = 100, delay: float = 0.3):
    """Re-enrich cards that have basic data but missing extended fields"""
    
    table_name = f"pokedata_cards_{lang}"
    stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Count cards that have category but no abilities (need extended enrichment)
        count_query = f"""
            SELECT COUNT(*) 
            FROM {table_name} 
            WHERE category IS NOT NULL AND category != ''
            AND (abilities IS NULL OR attacks IS NULL)
        """
        total = await conn.fetchval(count_query)
        
        print(f"🎴 Re-enriching {total:,} cards with extended fields...")
        print("=" * 60)
        
        async with httpx.AsyncClient() as client:
            offset = 0
            while offset < total:
                # Fetch batch of cards needing extended enrichment
                batch_query = f"""
                    SELECT id, tcgdex_id, name
                    FROM {table_name}
                    WHERE category IS NOT NULL AND category != ''
                    AND (abilities IS NULL OR attacks IS NULL)
                    ORDER BY id
                    LIMIT $1 OFFSET $2
                """
                
                cards = await conn.fetch(batch_query, batch_size, offset)
                
                if not cards:
                    break
                
                print(f"\n📦 Batch {offset // batch_size + 1} ({offset}-{offset + len(cards)} of {total})")
                
                for card in cards:
                    try:
                        # Fetch from TCGdex
                        url = f"{TCGDEX_BASE_URL}/{lang}/cards/{card['tcgdex_id']}"
                        response = await client.get(url, timeout=10.0)
                        
                        if response.status_code != 200:
                            stats['skipped'] += 1
                            continue
                        
                        tcgdex_data = response.json()
                        
                        # Prepare extended fields
                        abilities = json.dumps(tcgdex_data.get('abilities', [])) if tcgdex_data.get('abilities') else None
                        attacks = json.dumps(tcgdex_data.get('attacks', [])) if tcgdex_data.get('attacks') else None
                        weaknesses = json.dumps(tcgdex_data.get('weaknesses', [])) if tcgdex_data.get('weaknesses') else None
                        resistances = json.dumps(tcgdex_data.get('resistances', [])) if tcgdex_data.get('resistances') else None
                        variants = json.dumps(tcgdex_data.get('variants', {})) if tcgdex_data.get('variants') else None
                        suffix = tcgdex_data.get('suffix', None)
                        dex_id = tcgdex_data.get('dexId', None)
                        regulation_mark = tcgdex_data.get('regulationMark', None)
                        
                        # Update only extended fields
                        update_query = f"""
                            UPDATE {table_name}
                            SET 
                                abilities = $1::jsonb,
                                attacks = $2::jsonb,
                                weaknesses = $3::jsonb,
                                resistances = $4::jsonb,
                                variants = $5::jsonb,
                                suffix = $6,
                                dex_id = $7,
                                regulation_mark = $8
                            WHERE id = $9
                        """
                        
                        await conn.execute(
                            update_query,
                            abilities, attacks, weaknesses, resistances,
                            variants, suffix, dex_id, regulation_mark,
                            card['id']
                        )
                        
                        stats['success'] += 1
                        stats['total'] += 1
                        
                        # Log interesting cards
                        if abilities or attacks:
                            ability_count = len(tcgdex_data.get('abilities', []))
                            attack_count = len(tcgdex_data.get('attacks', []))
                            print(f"  ✓ {card['name']}: {ability_count} abilities, {attack_count} attacks")
                        
                        await asyncio.sleep(delay)
                        
                    except Exception as e:
                        stats['failed'] += 1
                        stats['total'] += 1
                        print(f"  ✗ Error on {card['name']}: {e}")
                
                offset += batch_size
                print(f"Progress: {stats['success']}/{total} ({stats['success']/total*100:.1f}%)")
        
    finally:
        await conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 Re-enrichment Complete!")
    print(f"Total: {stats['total']}")
    print(f"Success: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skipped: {stats['skipped']}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Re-enrich cards with extended fields')
    parser.add_argument('--lang', type=str, default='en', help='Language code')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size')
    parser.add_argument('--delay', type=float, default=0.3, help='Delay between requests')
    
    args = parser.parse_args()
    
    print("""
    🎴 TCGdex Extended Fields Re-enrichment
    =====================================
    This will add abilities, attacks, weaknesses, and resistances
    to cards that already have basic information.
    """)
    
    asyncio.run(re_enrich_extended_fields(args.lang, args.batch_size, args.delay))
