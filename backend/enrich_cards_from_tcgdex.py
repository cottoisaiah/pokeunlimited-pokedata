#!/usr/bin/env python3
"""
🎴 TCGdex Card Data Enrichment Script
Populates empty fields in pokedata_cards tables with data from TCGdex API
"""

import asyncio
import asyncpg
import httpx
import structlog
from typing import Optional, Dict, Any
import time
from datetime import datetime
import json

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Database configuration
DATABASE_URL = "postgresql://trading:trading@localhost:5432/tradingcards"

# TCGdex API
TCGDEX_BASE_URL = "https://api.tcgdex.net/v2"

# Supported languages
LANGUAGES = ['en', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'nl', 'pl', 'pt_br', 'ru', 'th', 'zh_cn', 'zh_tw', 'id']


class CardEnricher:
    """Enriches card data from TCGdex API"""
    
    def __init__(self, db_url: str, rate_limit_delay: float = 0.5):
        self.db_url = db_url
        self.rate_limit_delay = rate_limit_delay
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    async def fetch_card_from_tcgdex(
        self, 
        client: httpx.AsyncClient, 
        tcgdex_id: str, 
        lang: str = 'en'
    ) -> Optional[Dict[str, Any]]:
        """Fetch card data from TCGdex API"""
        try:
            url = f"{TCGDEX_BASE_URL}/{lang}/cards/{tcgdex_id}"
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Card not found in TCGdex: {tcgdex_id}")
                return None
            else:
                logger.error(f"TCGdex API error: {response.status_code} for {tcgdex_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching from TCGdex: {e}", tcgdex_id=tcgdex_id)
            return None
    
    async def enrich_card(
        self, 
        conn: asyncpg.Connection, 
        client: httpx.AsyncClient,
        card_id: int,
        tcgdex_id: str,
        table_name: str,
        lang: str = 'en'
    ) -> bool:
        """Enrich a single card with TCGdex data"""
        try:
            # Fetch from TCGdex
            tcgdex_data = await self.fetch_card_from_tcgdex(client, tcgdex_id, lang)
            
            if not tcgdex_data:
                self.stats['skipped'] += 1
                return False
            
            # Prepare update data - Basic fields
            update_data = {
                'category': tcgdex_data.get('category', ''),
                'rarity': tcgdex_data.get('rarity', ''),
                'illustrator': tcgdex_data.get('illustrator', ''),
                'hp': tcgdex_data.get('hp'),
                'types': json.dumps(tcgdex_data.get('types', [])),
                'stage': tcgdex_data.get('stage', ''),
                'evolves_from': tcgdex_data.get('evolveFrom', ''),
                'retreat_cost': tcgdex_data.get('retreat'),
                'image_url': tcgdex_data.get('image', ''),  # Add image URL
            }
            
            # Extended fields (Phase 2)
            update_data.update({
                'abilities': json.dumps(tcgdex_data.get('abilities', [])) if tcgdex_data.get('abilities') else None,
                'attacks': json.dumps(tcgdex_data.get('attacks', [])) if tcgdex_data.get('attacks') else None,
                'weaknesses': json.dumps(tcgdex_data.get('weaknesses', [])) if tcgdex_data.get('weaknesses') else None,
                'resistances': json.dumps(tcgdex_data.get('resistances', [])) if tcgdex_data.get('resistances') else None,
                'variants': json.dumps(tcgdex_data.get('variants', {})) if tcgdex_data.get('variants') else None,
                'suffix': tcgdex_data.get('suffix', None),
                'dex_id': tcgdex_data.get('dexId', None),  # Can be array or single int
                'regulation_mark': tcgdex_data.get('regulationMark', None),
            })
            
            # Update database with all fields
            query = f"""
                UPDATE {table_name}
                SET 
                    category = $1,
                    rarity = $2,
                    illustrator = $3,
                    hp = $4,
                    types = $5::jsonb,
                    stage = $6,
                    evolves_from = $7,
                    retreat_cost = $8,
                    abilities = $9::jsonb,
                    attacks = $10::jsonb,
                    weaknesses = $11::jsonb,
                    resistances = $12::jsonb,
                    variants = $13::jsonb,
                    suffix = $14,
                    dex_id = $15,
                    regulation_mark = $16,
                    image_url = COALESCE(image_url, $17)
                WHERE id = $18
            """
            
            await conn.execute(
                query,
                update_data['category'],
                update_data['rarity'],
                update_data['illustrator'],
                update_data['hp'],
                update_data['types'],
                update_data['stage'],
                update_data['evolves_from'],
                update_data['retreat_cost'],
                update_data['abilities'],
                update_data['attacks'],
                update_data['weaknesses'],
                update_data['resistances'],
                update_data['variants'],
                update_data['suffix'],
                update_data['dex_id'],
                update_data['regulation_mark'],
                update_data['image_url'],
                card_id
            )
            
            self.stats['successful'] += 1
            logger.info(
                "Card enriched successfully",
                card_id=card_id,
                tcgdex_id=tcgdex_id,
                name=tcgdex_data.get('name')
            )
            return True
            
        except Exception as e:
            self.stats['failed'] += 1
            self.stats['errors'].append({
                'card_id': card_id,
                'tcgdex_id': tcgdex_id,
                'error': str(e)
            })
            logger.error(f"Error enriching card: {e}", card_id=card_id, tcgdex_id=tcgdex_id)
            return False
    
    async def enrich_language(
        self, 
        lang: str, 
        batch_size: int = 100,
        max_cards: Optional[int] = None
    ):
        """Enrich all cards for a specific language"""
        table_name = f"pokedata_cards_{lang}"
        
        logger.info(f"Starting enrichment for language: {lang}", table=table_name)
        
        # Connect to database
        conn = await asyncpg.connect(self.db_url)
        
        try:
            # Get total count
            total_query = f"SELECT COUNT(*) FROM {table_name}"
            total_cards = await conn.fetchval(total_query)
            
            if max_cards:
                total_cards = min(total_cards, max_cards)
            
            logger.info(f"Total cards to process: {total_cards}")
            
            # Create HTTP client
            async with httpx.AsyncClient() as client:
                # Process in batches
                for offset in range(0, total_cards, batch_size):
                    batch_query = f"""
                        SELECT id, tcgdex_id, name
                        FROM {table_name}
                        WHERE category = '' OR category IS NULL
                        ORDER BY id
                        LIMIT $1 OFFSET $2
                    """
                    
                    cards = await conn.fetch(batch_query, batch_size, offset)
                    
                    if not cards:
                        break
                    
                    logger.info(
                        f"Processing batch {offset // batch_size + 1}",
                        cards_in_batch=len(cards),
                        progress=f"{offset}/{total_cards}"
                    )
                    
                    # Process each card in batch
                    for card in cards:
                        await self.enrich_card(
                            conn, 
                            client,
                            card['id'],
                            card['tcgdex_id'],
                            table_name,
                            lang
                        )
                        
                        self.stats['total_processed'] += 1
                        
                        # Rate limiting
                        await asyncio.sleep(self.rate_limit_delay)
                    
                    # Progress update
                    logger.info(
                        "Batch complete",
                        processed=self.stats['total_processed'],
                        successful=self.stats['successful'],
                        failed=self.stats['failed'],
                        skipped=self.stats['skipped']
                    )
                    
        finally:
            await conn.close()
    
    async def enrich_all_languages(
        self, 
        languages: list = None,
        batch_size: int = 100,
        max_cards: Optional[int] = None
    ):
        """Enrich cards for multiple languages"""
        languages = languages or ['en']
        
        logger.info("Starting multi-language enrichment", languages=languages)
        
        for lang in languages:
            logger.info(f"\n{'='*60}\nProcessing language: {lang}\n{'='*60}")
            
            try:
                await self.enrich_language(lang, batch_size, max_cards)
            except Exception as e:
                logger.error(f"Error processing language {lang}: {e}")
                continue
        
        # Final stats
        logger.info(
            "\n" + "="*60 + "\nEnrichment Complete\n" + "="*60,
            **self.stats
        )
        
        # Show errors if any
        if self.stats['errors']:
            logger.warning(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:10]:  # Show first 10
                logger.error("Error detail", **error)


async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich card data from TCGdex')
    parser.add_argument('--lang', type=str, default='en', help='Language code (default: en)')
    parser.add_argument('--all-langs', action='store_true', help='Process all languages')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size (default: 100)')
    parser.add_argument('--max-cards', type=int, default=None, help='Max cards to process (for testing)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (default: 0.5s)')
    parser.add_argument('--db-url', type=str, default=DATABASE_URL, help='Database URL')
    
    args = parser.parse_args()
    
    enricher = CardEnricher(args.db_url, rate_limit_delay=args.delay)
    
    if args.all_langs:
        await enricher.enrich_all_languages(
            languages=LANGUAGES,
            batch_size=args.batch_size,
            max_cards=args.max_cards
        )
    else:
        await enricher.enrich_language(
            lang=args.lang,
            batch_size=args.batch_size,
            max_cards=args.max_cards
        )


if __name__ == '__main__':
    print("""
    🎴 TCGdex Card Data Enrichment Script
    =====================================
    
    This script will populate empty card fields with data from TCGdex API.
    
    Usage examples:
      # Enrich English cards (first 10 for testing)
      python3 enrich_cards_from_tcgdex.py --lang en --max-cards 10
      
      # Enrich all English cards
      python3 enrich_cards_from_tcgdex.py --lang en
      
      # Enrich all languages
      python3 enrich_cards_from_tcgdex.py --all-langs
      
      # Custom batch size and delay
      python3 enrich_cards_from_tcgdex.py --lang en --batch-size 50 --delay 1.0
    
    """)
    
    asyncio.run(main())
