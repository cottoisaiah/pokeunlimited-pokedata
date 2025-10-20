#!/usr/bin/env python3
"""
💰 TCGdex Pricing Enrichment Script
Fetches pricing data from TCGdex API and updates database
"""

import asyncio
import asyncpg
import httpx
import structlog
from typing import Optional, Dict, Any
import json
from datetime import datetime

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


class PricingEnricher:
    """Enriches card pricing data from TCGdex API"""
    
    def __init__(self, db_url: str, rate_limit_delay: float = 0.5):
        self.db_url = db_url
        self.rate_limit_delay = rate_limit_delay
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'no_pricing': 0,
            'errors': []
        }
    
    async def fetch_card_pricing(
        self, 
        client: httpx.AsyncClient, 
        tcgdex_id: str, 
        lang: str = 'en'
    ) -> Optional[Dict[str, Any]]:
        """Fetch card pricing from TCGdex API"""
        try:
            url = f"{TCGDEX_BASE_URL}/{lang}/cards/{tcgdex_id}"
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                # Extract pricing data - it's under 'pricing' key in TCGdex response
                if 'pricing' in data:
                    pricing = data['pricing']
                    # Return pricing if either tcgplayer or cardmarket exists
                    if 'tcgplayer' in pricing or 'cardmarket' in pricing:
                        return pricing
                
                # No pricing found
                return None
            elif response.status_code == 404:
                logger.warning(f"Card not found in TCGdex: {tcgdex_id}")
                return None
            else:
                logger.error(f"TCGdex API error: {response.status_code} for {tcgdex_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching pricing from TCGdex: {e}", tcgdex_id=tcgdex_id)
            return None
    
    async def update_card_pricing(
        self, 
        conn: asyncpg.Connection, 
        client: httpx.AsyncClient,
        card_id: int,
        tcgdex_id: str,
        table_name: str,
        lang: str = 'en'
    ) -> bool:
        """Update pricing for a single card"""
        try:
            # Fetch pricing from TCGdex
            pricing_data = await self.fetch_card_pricing(client, tcgdex_id, lang)
            
            if not pricing_data:
                self.stats['no_pricing'] += 1
                return False
            
            # Prepare pricing update
            tcgplayer_prices = None
            cardmarket_prices = None
            
            if pricing_data.get('tcgplayer'):
                tcgplayer_prices = json.dumps(pricing_data['tcgplayer'])
            
            if pricing_data.get('cardmarket'):
                cardmarket_prices = json.dumps(pricing_data['cardmarket'])
            
            if not tcgplayer_prices and not cardmarket_prices:
                self.stats['no_pricing'] += 1
                return False
            
            # Update database
            query = f"""
                UPDATE {table_name}
                SET 
                    tcgplayer_prices = $1::jsonb,
                    cardmarket_prices = $2::jsonb,
                    pricing_last_updated = $3
                WHERE id = $4
            """
            
            await conn.execute(
                query,
                tcgplayer_prices,
                cardmarket_prices,
                datetime.utcnow(),
                card_id
            )
            
            self.stats['successful'] += 1
            
            # Log with pricing info
            pricing_info = []
            if tcgplayer_prices:
                pricing_info.append("TCGPlayer")
            if cardmarket_prices:
                pricing_info.append("CardMarket")
            
            logger.info(
                "Pricing updated successfully",
                card_id=card_id,
                tcgdex_id=tcgdex_id,
                sources=", ".join(pricing_info)
            )
            return True
            
        except Exception as e:
            self.stats['failed'] += 1
            self.stats['errors'].append({
                'card_id': card_id,
                'tcgdex_id': tcgdex_id,
                'error': str(e)
            })
            logger.error(f"Error updating pricing: {e}", card_id=card_id, tcgdex_id=tcgdex_id)
            return False
    
    async def enrich_language(
        self, 
        lang: str, 
        batch_size: int = 100,
        max_cards: Optional[int] = None,
        only_enriched: bool = True
    ):
        """Enrich pricing for all cards in a language"""
        table_name = f"pokedata_cards_{lang}"
        
        logger.info(f"Starting pricing enrichment for language: {lang}", table=table_name)
        
        # Connect to database
        conn = await asyncpg.connect(self.db_url)
        
        try:
            # Build query - only process cards that have been enriched
            where_clause = ""
            if only_enriched:
                where_clause = "WHERE category IS NOT NULL AND category != ''"
            
            # Get total count
            total_query = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
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
                        {where_clause}
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
                        await self.update_card_pricing(
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
                        no_pricing=self.stats['no_pricing']
                    )
                    
        finally:
            await conn.close()
    
    async def enrich_all_languages(
        self, 
        languages: list = None,
        batch_size: int = 100,
        max_cards: Optional[int] = None
    ):
        """Enrich pricing for multiple languages"""
        languages = languages or ['en']
        
        logger.info("Starting multi-language pricing enrichment", languages=languages)
        
        for lang in languages:
            logger.info(f"\n{'='*60}\nProcessing language: {lang}\n{'='*60}")
            
            try:
                await self.enrich_language(lang, batch_size, max_cards)
            except Exception as e:
                logger.error(f"Error processing language {lang}: {e}")
                continue
        
        # Final stats
        logger.info(
            "\n" + "="*60 + "\nPricing Enrichment Complete\n" + "="*60,
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
    
    parser = argparse.ArgumentParser(description='Enrich card pricing from TCGdex')
    parser.add_argument('--lang', type=str, default='en', help='Language code (default: en)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size (default: 100)')
    parser.add_argument('--max-cards', type=int, default=None, help='Max cards to process (for testing)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (default: 0.5s)')
    parser.add_argument('--db-url', type=str, default=DATABASE_URL, help='Database URL')
    parser.add_argument('--all', action='store_true', help='Process all enriched cards (ignore pricing_last_updated)')
    
    args = parser.parse_args()
    
    enricher = PricingEnricher(args.db_url, rate_limit_delay=args.delay)
    
    await enricher.enrich_language(
        lang=args.lang,
        batch_size=args.batch_size,
        max_cards=args.max_cards,
        only_enriched=True
    )


if __name__ == '__main__':
    print("""
    💰 TCGdex Pricing Enrichment Script
    ===================================
    
    This script will fetch pricing data from TCGdex API and update the database.
    
    Usage examples:
      # Update pricing for first 10 English cards (testing)
      python3 enrich_pricing_from_tcgdex.py --lang en --max-cards 10
      
      # Update all English card pricing
      python3 enrich_pricing_from_tcgdex.py --lang en
      
      # Custom batch size and delay
      python3 enrich_pricing_from_tcgdex.py --lang en --batch-size 50 --delay 1.0
    
    """)
    
    asyncio.run(main())
