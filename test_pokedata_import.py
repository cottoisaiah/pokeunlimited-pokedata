#!/usr/bin/env python3
"""
🧪 PokeData Import Service Test
Test the TCGdex data import functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.pokedata_import_service import PokeDataImportService


async def test_import_service():
    """Test the import service with a small dataset"""
    print("🧪 Testing PokeData Import Service...")

    service = PokeDataImportService()

    # Test importing just English data with limit
    print("📦 Testing English import (limited to 2 sets)...")
    try:
        stats = await service.import_language('en', limit_sets=2)
        print("✅ English import test passed!")
        print(f"   Sets processed: {stats.sets_processed}")
        print(f"   Cards processed: {stats.cards_processed}")
        print(f"   Duration: {stats.duration}")
    except Exception as e:
        print(f"❌ English import test failed: {e}")
        return False

    # Test eBay pricing update (limited)
    print("\n💰 Testing eBay pricing update (limited to 5 cards)...")
    try:
        results = await service.update_ebay_pricing(limit=5)
        print("✅ eBay pricing test passed!")
        print(f"   Cards updated: {results['updated']}")
        print(f"   Errors: {results['errors']}")
    except Exception as e:
        print(f"❌ eBay pricing test failed: {e}")
        return False

    print("\n🎉 All tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_import_service())
    sys.exit(0 if success else 1)