#!/usr/bin/env python3
"""
🎯 PokeData Import Manager
Command-line tool for managing TCGdex data imports and eBay pricing updates
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.pokedata_import_service import (
    import_all_pokedata,
    import_pokedata_language,
    update_all_ebay_pricing
)


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def import_command(args):
    """Handle import command"""
    print("🚀 Starting PokeData import...")

    if args.language:
        print(f"📦 Importing data for language: {args.language}")
        stats = await import_pokedata_language(args.language, args.limit_sets)
        print_import_stats(args.language, stats)
    else:
        print("📦 Importing data for all languages (EN, JA, ZH, KO)")
        results = await import_all_pokedata(args.limit_sets)
        for lang, stats in results.items():
            print_import_stats(lang, stats)


def print_import_stats(language: str, stats):
    """Print import statistics"""
    print(f"\n📊 Import Statistics for {language.upper()}:")
    print(f"   Sets processed: {stats.sets_processed}")
    print(f"   Cards processed: {stats.cards_processed}")
    print(f"   Cards created: {stats.cards_created}")
    print(f"   Cards updated: {stats.cards_updated}")
    print(f"   Errors: {stats.errors}")
    if stats.duration:
        print(f"   Duration: {stats.duration}")
        print(f"   Cards/second: {stats.cards_per_second:.2f}")


async def pricing_command(args):
    """Handle pricing update command"""
    print("💰 Starting eBay pricing update...")

    results = await update_all_ebay_pricing(args.limit)

    print("\n📊 Pricing Update Results:")
    print(f"   Cards updated: {results['updated']}")
    print(f"   Errors: {results['errors']}")


async def status_command(args):
    """Handle status command"""
    print("📋 PokeData Import Status")

    # Import here to avoid circular imports
    from app.models.database import get_db_session
    from app.models.pokedata_models import PokeDataCard, PokeDataSet
    from sqlalchemy import select, func

    async with get_db_session() as session:
        # Count sets by language
        set_counts = await session.execute(
            select(PokeDataSet.language, func.count(PokeDataSet.id)).group_by(PokeDataSet.language)
        )
        set_counts = dict(set_counts.all())

        # Count cards by language
        card_counts = await session.execute(
            select(PokeDataCard.language, func.count(PokeDataCard.id)).group_by(PokeDataCard.language)
        )
        card_counts = dict(card_counts.all())

        # Count cards with pricing
        priced_cards = await session.execute(
            select(func.count(PokeDataCard.id)).where(PokeDataCard.is_priced == True)
        )
        priced_count = priced_cards.scalar()

        total_cards = sum(card_counts.values())

        print("\n📊 Database Status:")
        print(f"   Total sets: {sum(set_counts.values())}")
        print(f"   Total cards: {total_cards}")
        print(f"   Priced cards: {priced_count} ({priced_count/total_cards*100:.1f}%)" if total_cards > 0 else "")

        print("\n🌍 By Language:")
        for lang in ['en', 'ja', 'zh', 'ko']:
            sets = set_counts.get(lang, 0)
            cards = card_counts.get(lang, 0)
            print(f"   {lang.upper()}: {sets} sets, {cards} cards")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="PokeData Import Manager - Manage TCGdex data imports and eBay pricing"
    )

    # Global options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import TCGdex data")
    import_parser.add_argument(
        "--language",
        choices=["en", "ja", "zh", "ko"],
        help="Import only specific language (default: all languages)"
    )
    import_parser.add_argument(
        "--limit-sets",
        type=int,
        help="Limit number of sets to import per language (for testing)"
    )

    # Pricing command
    pricing_parser = subparsers.add_parser("pricing", help="Update eBay pricing data")
    pricing_parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of cards to update (for testing)"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show database status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Setup logging
    setup_logging(args.log_level)

    # Run the appropriate command
    try:
        if args.command == "import":
            asyncio.run(import_command(args))
        elif args.command == "pricing":
            asyncio.run(pricing_command(args))
        elif args.command == "status":
            asyncio.run(status_command(args))
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()