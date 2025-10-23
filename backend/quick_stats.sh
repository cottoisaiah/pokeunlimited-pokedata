#!/bin/bash
# Quick stats check - compact version

cd /home/ubuntu/opt/app/pokeunlimited-pokedata/backend

python3 -c "
import asyncio
import asyncpg

async def quick_stats():
    conn = await asyncpg.connect('postgresql://trading:trading@localhost:5432/tradingcards')
    
    stats = await conn.fetchrow('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN abilities IS NOT NULL THEN 1 END) as extended,
            COUNT(CASE WHEN tcgplayer_prices IS NOT NULL THEN 1 END) as pricing
        FROM pokedata_cards_en
    ''')
    
    total = stats['total']
    extended = stats['extended']
    pricing = stats['pricing']
    
    ext_pct = (extended / total * 100) if total > 0 else 0
    price_pct = (pricing / total * 100) if total > 0 else 0
    
    print(f'📊 Extended: {extended:,}/{total:,} ({ext_pct:.1f}%)  |  💰 Pricing: {pricing:,}/{total:,} ({price_pct:.1f}%)')
    
    await conn.close()

asyncio.run(quick_stats())
"
