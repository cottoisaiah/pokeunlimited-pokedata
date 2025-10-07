#!/usr/bin/env python3
"""
🧪 TCGdex SDK Test
Test basic TCGdex SDK functionality without database
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import tcgdexsdk


async def test_tcgdex_sdk():
    """Test basic TCGdex SDK functionality"""
    print("🧪 Testing TCGdex SDK...")

    try:
        # Test English client
        print("📦 Testing English TCGdex client...")
        client_en = tcgdexsdk.TCGdex(tcgdexsdk.Language.EN)

        # Get sets
        sets = await client_en.set.list()
        print(f"✅ Found {len(sets)} English sets")

        if sets:
            # Test first set
            first_set = sets[0]
            print(f"   First set: {first_set.name} (ID: {first_set.id})")

            # Test getting cards from first set
            query = tcgdexsdk.Query()
            query.set = first_set.id
            cards = await client_en.card.list(query)
            print(f"   Cards in first set: {len(cards)}")

        # Test Japanese client
        print("📦 Testing Japanese TCGdex client...")
        client_ja = tcgdexsdk.TCGdex(tcgdexsdk.Language.JA)
        sets_ja = await client_ja.set.list()
        print(f"✅ Found {len(sets_ja)} Japanese sets")

        print("🎉 TCGdex SDK test passed!")
        return True

    except Exception as e:
        print(f"❌ TCGdex SDK test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_tcgdex_sdk())
    sys.exit(0 if success else 1)