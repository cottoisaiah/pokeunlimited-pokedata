#!/usr/bin/env python3
"""
Fix logo URLs for non-English sets by using English logo URLs directly.
TCGdex only hosts logos at English paths, not language-specific paths.
"""

import asyncio
import asyncpg

async def fix_logo_urls():
    """Copy English logo URLs to non-English sets without changing the path."""
    
    conn = await asyncpg.connect(
        host='localhost',
        database='tradingcards',
        user='trading',
        password='trading'
    )
    
    # Languages to fix (all except English)
    languages = ['ja', 'de', 'es', 'fr', 'it', 'ko', 'nl', 'pl', 'pt_br', 'ru', 'th', 'zh_cn', 'zh_tw', 'id']
    
    print("Fixing logo URLs to use English asset paths...\n")
    
    for lang in languages:
        lang_table = f'pokedata_sets_{lang}'
        
        try:
            # Update logo URLs to use English paths directly
            # This replaces language-specific paths with English paths
            result = await conn.execute(f"""
                UPDATE {lang_table} AS target
                SET logo_url = source.logo_url
                FROM pokedata_sets_en AS source
                WHERE target.tcgdex_id = source.tcgdex_id
                  AND source.logo_url IS NOT NULL
                  AND source.logo_url != ''
            """)
            
            print(f"{lang.upper()}: {result}")
            
        except Exception as e:
            print(f"{lang.upper()}: ERROR - {e}")
    
    await conn.close()
    print("\nLogo URL fix complete!")

if __name__ == "__main__":
    asyncio.run(fix_logo_urls())
