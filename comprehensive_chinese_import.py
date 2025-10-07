#!/usr/bin/env python3
"""
🎯 Comprehensive Multi-Language Pokemon TCG Import
Import Pokemon TCG data from TCGdex API for Chinese languages using ORM
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import get_db_session
from app.models.pokedata_models import PokeDataSet, PokeDataCard
from app.services.tcgdex_service import TCGdexClient, Language


class ImportStats:
    """Statistics for import operations"""
    def __init__(self):
        self.sets_imported = 0
        self.cards_imported = 0
        self.errors = 0
        self.start_time = datetime.now()

    def duration(self):
        return datetime.now() - self.start_time


def serialize_tcgdex_object(obj: Any) -> Dict[str, Any]:
    """Serialize TCGdex object to JSON-compatible dict"""
    try:
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return {}
    except:
        return {}


async def import_language_data_orm(lang_code: str, lang_url_code: str, limit_sets: Optional[int] = None) -> ImportStats:
    """Import data for a specific language using ORM"""
    stats = ImportStats()
    
    try:
        print(f"🌍 Starting import for {lang_code}...")

        # Initialize TCGdex client
        async with TCGdexClient(lang_url_code) as client:
            # Get sets
            sets = await client.get_sets()
            if limit_sets:
                sets = sets[:limit_sets]

            print(f"📦 Found {len(sets)} sets for {lang_code}")

            async with get_db_session() as session:
                for set_info in sets:
                    try:
                        # Check if set already exists
                        existing_set = await session.execute(
                            select(PokeDataSet).where(
                                PokeDataSet.tcgdex_id == set_info.id,
                                PokeDataSet.language == lang_code
                            )
                        )
                        existing_set = existing_set.scalar_one_or_none()

                        if not existing_set:
                            # Create new set
                            pokedata_set = PokeDataSet(
                                tcgdex_id=set_info.id,
                                name=set_info.name,
                                code=getattr(set_info, 'code', None),
                                language=lang_code,
                                release_date=getattr(set_info, 'release_date', None),
                                total_cards=set_info.card_count.get('total', 0) if isinstance(set_info.card_count, dict) else set_info.card_count,
                                logo_url=getattr(set_info, 'image', None),
                                symbol_url=getattr(set_info, 'symbol', None),
                                serie_name=getattr(set_info, 'series', None),
                                raw_tcgdex_data=serialize_tcgdex_object(set_info)
                            )
                            session.add(pokedata_set)
                            stats.sets_imported += 1
                        else:
                            # Update existing set
                            existing_set.name = set_info.name
                            existing_set.code = getattr(set_info, 'code', None)
                            existing_set.release_date = getattr(set_info, 'release_date', None)
                            existing_set.total_cards = set_info.card_count.get('total', 0) if isinstance(set_info.card_count, dict) else set_info.card_count
                            existing_set.logo_url = getattr(set_info, 'image', None)
                            existing_set.symbol_url = getattr(set_info, 'symbol', None)
                            existing_set.serie_name = getattr(set_info, 'series', None)
                            existing_set.raw_tcgdex_data = serialize_tcgdex_object(set_info)
                            existing_set.updated_at = datetime.now()
                            stats.sets_imported += 1

                        print(f"   ✅ {set_info.name} ({set_info.id})")

                    except Exception as e:
                        print(f"❌ Error importing set {set_info.id}: {e}")
                        stats.errors += 1
                        continue

                await session.commit()

        print(f"✅ Completed {lang_code}: {stats.sets_imported} sets in {stats.duration()}")
        return stats

    except Exception as e:
        print(f"❌ Fatal error importing {lang_code}: {e}")
        stats.errors += 1
        return stats


async def main():
    """Main import function"""
    print("🎯 COMPREHENSIVE CHINESE POKEMON TCG IMPORT")
    print("=" * 60)

    # Chinese languages
    languages = {
        'zh_cn': 'zh-cn',  # Chinese Simplified
        'zh_tw': 'zh-tw',  # Chinese Traditional
    }

    total_stats = {}
    limit_sets = None  # Set to a number to limit sets per language for testing

    for lang_code, lang_url_code in languages.items():
        try:
            stats = await import_language_data_orm(lang_code, lang_url_code, limit_sets)
            total_stats[lang_code] = stats
        except Exception as e:
            print(f"❌ Failed to import {lang_code}: {e}")
            continue

    # Print summary
    print("\\n" + "=" * 60)
    print("📊 IMPORT SUMMARY")
    print("=" * 60)

    total_sets = sum(stats.sets_imported for stats in total_stats.values())
    total_cards = sum(stats.cards_imported for stats in total_stats.values())
    total_errors = sum(stats.errors for stats in total_stats.values())

    for lang_code, stats in total_stats.items():
        status = "✅" if stats.errors == 0 else "⚠️"
        print(f"{status} {lang_code.upper()}: {stats.sets_imported} sets, {stats.cards_imported} cards")

    print(f"\\n🎯 GRAND TOTAL: {total_sets} sets, {total_cards} cards across {len(total_stats)} languages")
    if total_errors > 0:
        print(f"⚠️  Total errors: {total_errors}")


if __name__ == "__main__":
    asyncio.run(main())