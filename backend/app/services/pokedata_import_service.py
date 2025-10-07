"""
🎯 PokeData Import Service
Fetch and store TCGdex card data with eBay pricing for multiple languages
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass

import structlog
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import tcgdexsdk
from app.models.database import get_db_session
from app.models.pokedata_models import PokeDataCard, PokeDataSet
from app.services.ebay_service import EnhancedeBayService

logger = structlog.get_logger(__name__)


@dataclass
class ImportStats:
    """Statistics for data import operations"""
    sets_processed: int = 0
    cards_processed: int = 0
    cards_created: int = 0
    cards_updated: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> Optional[timedelta]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def cards_per_second(self) -> float:
        if self.duration and self.duration.total_seconds() > 0:
            return self.cards_processed / self.duration.total_seconds()
        return 0.0


class PokeDataImportService:
    """Service for importing TCGdex data with eBay pricing"""

    SUPPORTED_LANGUAGES = {
        'en': tcgdexsdk.Language.EN,
        'ja': tcgdexsdk.Language.JA,
        'zh': tcgdexsdk.Language.ZH_CN,
        'ko': tcgdexsdk.Language.KO
    }

    def __init__(self):
        self.clients = {}
        self.ebay_service = EnhancedeBayService()
        self._init_clients()

    def _init_clients(self):
        """Initialize TCGdex clients for all supported languages"""
        for lang_code, lang_enum in self.SUPPORTED_LANGUAGES.items():
            self.clients[lang_code] = tcgdexsdk.TCGdex(lang_enum)
            logger.info(f"Initialized TCGdex client for {lang_code}")

    async def import_all_languages(self, limit_sets: Optional[int] = None) -> Dict[str, ImportStats]:
        """Import data for all supported languages"""
        results = {}

        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            logger.info(f"Starting import for language: {lang_code}")
            stats = await self.import_language(lang_code, limit_sets)
            results[lang_code] = stats
            logger.info(f"Completed import for {lang_code}: {stats.cards_processed} cards")

        return results

    async def import_language(self, language: str, limit_sets: Optional[int] = None) -> ImportStats:
        """Import data for a specific language"""
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        stats = ImportStats(start_time=datetime.now())
        client = self.clients[language]

        try:
            # Fetch all sets
            logger.info(f"Fetching sets for language {language}")
            sets = await client.set.list()

            if limit_sets:
                sets = sets[:limit_sets]

            stats.sets_processed = len(sets)
            logger.info(f"Found {len(sets)} sets for {language}")

            # Process each set
            for set_data in sets:
                try:
                    await self._import_set_with_cards(client, set_data, language, stats)
                except Exception as e:
                    logger.error(f"Error importing set {set_data.id}: {e}")
                    stats.errors += 1

        except Exception as e:
            logger.error(f"Error importing language {language}: {e}")
            stats.errors += 1

        stats.end_time = datetime.now()
        return stats

    async def _import_set_with_cards(self, client: tcgdexsdk.TCGdex, set_data: Any, language: str, stats: ImportStats):
        """Import a set and all its cards"""
        async with get_db_session() as session:
            # Check if set already exists
            existing_set = await session.execute(
                select(PokeDataSet).where(
                    and_(
                        PokeDataSet.tcgdex_id == set_data.id,
                        PokeDataSet.language == language
                    )
                )
            )
            existing_set = existing_set.scalar_one_or_none()

            if not existing_set:
                # Create new set
                pokedata_set = PokeDataSet(
                    tcgdex_id=set_data.id,
                    name=set_data.name,
                    code=getattr(set_data, 'code', None),
                    language=language,
                    release_date=getattr(set_data, 'releaseDate', None),
                    total_cards=getattr(set_data, 'cardCount', {}).get('total', 0) if hasattr(set_data, 'cardCount') else 0,
                    logo_url=getattr(set_data, 'logo', None),
                    symbol_url=getattr(set_data, 'symbol', None),
                    serie_name=getattr(set_data, 'serie', {}).get('name', None) if hasattr(set_data, 'serie') else None,
                    serie_code=getattr(set_data, 'serie', {}).get('code', None) if hasattr(set_data, 'serie') else None,
                    raw_tcgdex_data=self._serialize_tcgdex_object(set_data)
                )
                session.add(pokedata_set)
                await session.flush()  # Get the ID
            else:
                pokedata_set = existing_set

            # Fetch and import cards for this set
            await self._import_set_cards(client, set_data, pokedata_set, language, stats)

            await session.commit()

    async def _import_set_cards(self, client: tcgdexsdk.TCGdex, set_data: Any, pokedata_set: PokeDataSet, language: str, stats: ImportStats):
        """Import all cards from a set"""
        try:
            # Create query to filter by set
            query = tcgdexsdk.Query()
            query.set = set_data.id

            # Fetch cards
            cards = await client.card.list(query)
            logger.info(f"Fetched {len(cards)} cards for set {set_data.id} ({language})")

            async with get_db_session() as session:
                for card_data in cards:
                    try:
                        await self._import_card(card_data, pokedata_set, language, session, stats)
                    except Exception as e:
                        logger.error(f"Error importing card {getattr(card_data, 'id', 'unknown')}: {e}")
                        stats.errors += 1

                await session.commit()

        except Exception as e:
            logger.error(f"Error fetching cards for set {set_data.id}: {e}")
            stats.errors += 1

    async def _import_card(self, card_data: Any, pokedata_set: PokeDataSet, language: str, session: AsyncSession, stats: ImportStats):
        """Import a single card"""
        stats.cards_processed += 1

        # Check if card already exists
        existing_card = await session.execute(
            select(PokeDataCard).where(
                and_(
                    PokeDataCard.tcgdex_id == card_data.id,
                    PokeDataCard.language == language
                )
            )
        )
        existing_card = existing_card.scalar_one_or_none()

        # Extract card data
        card_info = self._extract_card_info(card_data, pokedata_set, language)

        if existing_card:
            # Update existing card
            for key, value in card_info.items():
                if hasattr(existing_card, key):
                    setattr(existing_card, key, value)
            existing_card.updated_at = datetime.now()
            existing_card.raw_tcgdex_data = self._serialize_tcgdex_object(card_data)
            stats.cards_updated += 1
        else:
            # Create new card
            new_card = PokeDataCard(**card_info)
            session.add(new_card)
            stats.cards_created += 1

    def _extract_card_info(self, card_data: Any, pokedata_set: PokeDataSet, language: str) -> Dict[str, Any]:
        """Extract card information from TCGdex card object"""
        return {
            'tcgdex_id': card_data.id,
            'local_id': getattr(card_data, 'localId', ''),
            'name': card_data.name,
            'language': language,
            'pokedata_set_id': pokedata_set.id,  # Foreign key to PokeDataSet
            'set_id': pokedata_set.tcgdex_id,
            'set_name': pokedata_set.name,
            'set_code': pokedata_set.code,
            'set_release_date': pokedata_set.release_date,
            'set_total_cards': pokedata_set.total_cards,
            'category': getattr(card_data, 'category', {}).get('name', '') if hasattr(card_data, 'category') else '',
            'rarity': getattr(card_data, 'rarity', {}).get('name', '') if hasattr(card_data, 'rarity') else '',
            'illustrator': getattr(card_data, 'illustrator', ''),
            'hp': getattr(card_data, 'hp', None),
            'types': [t.name for t in getattr(card_data, 'types', [])] if hasattr(card_data, 'types') else [],
            'stage': getattr(card_data, 'stage', ''),
            'evolves_from': getattr(card_data, 'evolvesFrom', ''),
            'retreat_cost': getattr(card_data, 'retreat', None),
            'image_url': card_data.image if hasattr(card_data, 'image') else '',
            'variants': self._extract_variants(card_data),
            'legal': self._extract_legal_info(card_data),
            'raw_tcgdex_data': self._serialize_tcgdex_object(card_data),
            'abilities': self._extract_abilities(card_data),
            'attacks': self._extract_attacks(card_data),
            'weaknesses': self._extract_weaknesses(card_data),
            'resistances': self._extract_resistances(card_data)
        }

    def _extract_variants(self, card_data: Any) -> Dict[str, bool]:
        """Extract card variants"""
        variants = {}
        if hasattr(card_data, 'variants'):
            variants_obj = card_data.variants
            variants = {
                'normal': getattr(variants_obj, 'normal', False),
                'reverse': getattr(variants_obj, 'reverse', False),
                'holo': getattr(variants_obj, 'holo', False),
                'firstEdition': getattr(variants_obj, 'firstEdition', False)
            }
        return variants

    def _extract_legal_info(self, card_data: Any) -> Dict[str, bool]:
        """Extract legal information"""
        legal = {}
        if hasattr(card_data, 'legal'):
            legal_obj = card_data.legal
            legal = {
                'standard': getattr(legal_obj, 'standard', False),
                'expanded': getattr(legal_obj, 'expanded', False)
            }
        return legal

    def _extract_abilities(self, card_data: Any) -> List[Dict[str, Any]]:
        """Extract abilities information"""
        abilities = []
        if hasattr(card_data, 'abilities'):
            for ability in card_data.abilities:
                abilities.append({
                    'type': getattr(ability, 'type', ''),
                    'name': getattr(ability, 'name', ''),
                    'effect': getattr(ability, 'effect', '')
                })
        return abilities

    def _extract_attacks(self, card_data: Any) -> List[Dict[str, Any]]:
        """Extract attacks information"""
        attacks = []
        if hasattr(card_data, 'attacks'):
            for attack in card_data.attacks:
                attacks.append({
                    'name': getattr(attack, 'name', ''),
                    'cost': [c.name for c in getattr(attack, 'cost', [])] if hasattr(attack, 'cost') else [],
                    'damage': getattr(attack, 'damage', ''),
                    'effect': getattr(attack, 'effect', '')
                })
        return attacks

    def _extract_weaknesses(self, card_data: Any) -> List[Dict[str, Any]]:
        """Extract weaknesses information"""
        weaknesses = []
        if hasattr(card_data, 'weaknesses'):
            for weakness in card_data.weaknesses:
                weaknesses.append({
                    'type': getattr(weakness, 'type', '').name if hasattr(weakness, 'type') else '',
                    'value': getattr(weakness, 'value', '')
                })
        return weaknesses

    def _extract_resistances(self, card_data: Any) -> List[Dict[str, Any]]:
        """Extract resistances information"""
        resistances = []
        if hasattr(card_data, 'resistances'):
            for resistance in card_data.resistances:
                resistances.append({
                    'type': getattr(resistance, 'type', '').name if hasattr(resistance, 'type') else '',
                    'value': getattr(resistance, 'value', '')
                })
        return resistances

    def _serialize_tcgdex_object(self, obj: Any) -> Dict[str, Any]:
        """Serialize TCGdex object to JSON-compatible dict"""
        try:
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            return {}
        except:
            return {}

    async def update_ebay_pricing(self, limit: Optional[int] = None) -> Dict[str, int]:
        """Update eBay pricing for cards in the database"""
        logger.info("Starting eBay pricing update")

        async with get_db_session() as session:
            # Get cards that need pricing updates (no pricing or old pricing)
            query = select(PokeDataCard).where(
                or_(
                    PokeDataCard.ebay_avg_price.is_(None),
                    PokeDataCard.last_ebay_update.is_(None),
                    PokeDataCard.last_ebay_update < datetime.now() - timedelta(days=1)
                )
            ).limit(limit) if limit else select(PokeDataCard).where(
                or_(
                    PokeDataCard.ebay_avg_price.is_(None),
                    PokeDataCard.last_ebay_update.is_(None),
                    PokeDataCard.last_ebay_update < datetime.now() - timedelta(days=1)
                )
            )

            result = await session.execute(query)
            cards = result.scalars().all()

            logger.info(f"Found {len(cards)} cards needing eBay pricing updates")

            updated = 0
            errors = 0

            for card in cards:
                try:
                    # Search eBay for this card
                    search_term = f'"{card.name}" "{card.set_name}" Pokemon TCG'
                    if card.language != 'en':
                        search_term += f' {card.language.upper()}'

                    ebay_results = await self.ebay_service.search_items(search_term, limit=50)

                    if ebay_results:
                        # Calculate average price from sold listings
                        sold_prices = []
                        active_prices = []

                        for item in ebay_results:
                            if item.get('sellingState') == 'EndedWithSales':
                                price = float(item.get('currentPrice', {}).get('value', 0))
                                if price > 0:
                                    sold_prices.append(price)
                            else:
                                price = float(item.get('currentPrice', {}).get('value', 0))
                                if price > 0:
                                    active_prices.append(price)

                        # Update card with pricing data
                        if sold_prices:
                            card.ebay_avg_price = sum(sold_prices) / len(sold_prices)
                            card.ebay_median_price = sorted(sold_prices)[len(sold_prices) // 2]
                            card.ebay_low_price = min(sold_prices)
                            card.ebay_high_price = max(sold_prices)
                            card.ebay_sold_count_30d = len(sold_prices)

                        if active_prices:
                            card.ebay_active_listings = len(active_prices)

                        card.last_ebay_update = datetime.now()
                        card.is_priced = True
                        updated += 1

                        # Calculate market price (simple average for now)
                        if card.ebay_avg_price:
                            card.market_price = card.ebay_avg_price

                    await asyncio.sleep(0.1)  # Rate limiting

                except Exception as e:
                    logger.error(f"Error updating eBay pricing for card {card.tcgdex_id}: {e}")
                    errors += 1

            await session.commit()

            logger.info(f"Updated eBay pricing for {updated} cards, {errors} errors")
            return {'updated': updated, 'errors': errors}


# Global instance
pokedata_import_service = PokeDataImportService()


async def import_all_pokedata(limit_sets: Optional[int] = None) -> Dict[str, ImportStats]:
    """Convenience function to import all PokeData"""
    return await pokedata_import_service.import_all_languages(limit_sets)


async def import_pokedata_language(language: str, limit_sets: Optional[int] = None) -> ImportStats:
    """Convenience function to import PokeData for specific language"""
    return await pokedata_import_service.import_language(language, limit_sets)


async def update_all_ebay_pricing(limit: Optional[int] = None) -> Dict[str, int]:
    """Convenience function to update all eBay pricing"""
    return await pokedata_import_service.update_ebay_pricing(limit)