#!/bin/bash
# Monitor both card enrichment and pricing enrichment processes

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to get enrichment stats
get_stats() {
    python3 -c "
import asyncio
import asyncpg
from datetime import datetime

async def check():
    conn = await asyncpg.connect('postgresql://trading:trading@localhost:5432/tradingcards')
    
    # Get overall stats
    stats = await conn.fetchrow('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN category IS NOT NULL THEN 1 END) as enriched_basic,
            COUNT(CASE WHEN abilities IS NOT NULL THEN 1 END) as enriched_extended,
            COUNT(CASE WHEN tcgplayer_prices IS NOT NULL THEN 1 END) as enriched_pricing
        FROM pokedata_cards_en
    ''')
    
    # Get latest extended enrichment
    latest_extended = await conn.fetchrow('''
        SELECT id, name, tcgdex_id
        FROM pokedata_cards_en
        WHERE abilities IS NOT NULL
        ORDER BY id DESC
        LIMIT 1
    ''')
    
    # Get latest pricing enrichment
    latest_pricing = await conn.fetchrow('''
        SELECT id, name, tcgdex_id, pricing_last_updated
        FROM pokedata_cards_en
        WHERE tcgplayer_prices IS NOT NULL OR cardmarket_prices IS NOT NULL
        ORDER BY pricing_last_updated DESC
        LIMIT 1
    ''')
    
    total = stats['total']
    basic = stats['enriched_basic']
    extended = stats['enriched_extended']
    pricing = stats['enriched_pricing']
    
    print(f'TOTAL:{total}')
    print(f'BASIC:{basic}')
    print(f'EXTENDED:{extended}')
    print(f'PRICING:{pricing}')
    
    if latest_extended:
        print(f'LATEST_EXT_ID:{latest_extended[\"id\"]}')
        print(f'LATEST_EXT_NAME:{latest_extended[\"name\"]}')
        print(f'LATEST_EXT_TCGDEX:{latest_extended[\"tcgdex_id\"]}')
    
    if latest_pricing:
        print(f'LATEST_PRICE_ID:{latest_pricing[\"id\"]}')
        print(f'LATEST_PRICE_NAME:{latest_pricing[\"name\"]}')
        print(f'LATEST_PRICE_TCGDEX:{latest_pricing[\"tcgdex_id\"]}')
        if latest_pricing['pricing_last_updated']:
            print(f'LATEST_PRICE_TIME:{latest_pricing[\"pricing_last_updated\"]}')
    
    await conn.close()

asyncio.run(check())
"
}

clear
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         Pokemon Card Enrichment Status Monitor                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📊 Checking database status...${NC}"
echo ""

# Get stats
STATS=$(get_stats)

# Parse stats
TOTAL=$(echo "$STATS" | grep "TOTAL:" | cut -d: -f2)
BASIC=$(echo "$STATS" | grep "BASIC:" | cut -d: -f2)
EXTENDED=$(echo "$STATS" | grep "EXTENDED:" | cut -d: -f2)
PRICING=$(echo "$STATS" | grep "PRICING:" | cut -d: -f2)

LATEST_EXT_ID=$(echo "$STATS" | grep "LATEST_EXT_ID:" | cut -d: -f2)
LATEST_EXT_NAME=$(echo "$STATS" | grep "LATEST_EXT_NAME:" | cut -d: -f2)
LATEST_EXT_TCGDEX=$(echo "$STATS" | grep "LATEST_EXT_TCGDEX:" | cut -d: -f2)

LATEST_PRICE_ID=$(echo "$STATS" | grep "LATEST_PRICE_ID:" | cut -d: -f2)
LATEST_PRICE_NAME=$(echo "$STATS" | grep "LATEST_PRICE_NAME:" | cut -d: -f2)
LATEST_PRICE_TCGDEX=$(echo "$STATS" | grep "LATEST_PRICE_TCGDEX:" | cut -d: -f2)

# Calculate percentages
BASIC_PCT=$(echo "scale=1; $BASIC * 100 / $TOTAL" | bc)
EXTENDED_PCT=$(echo "scale=1; $EXTENDED * 100 / $TOTAL" | bc)
PRICING_PCT=$(echo "scale=1; $PRICING * 100 / $TOTAL" | bc)

# Database Stats
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}📦 DATABASE STATISTICS${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
printf "%-25s %s\n" "Total Cards:" "$(printf '%s' "$TOTAL" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')"
printf "%-25s %s (%s%%)\n" "Basic Enrichment:" "$(printf '%s' "$BASIC" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')" "$BASIC_PCT"
printf "%-25s %s (%s%%)\n" "Extended Enrichment:" "$(printf '%s' "$EXTENDED" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')" "$EXTENDED_PCT"
printf "%-25s %s (%s%%)\n" "Pricing Enrichment:" "$(printf '%s' "$PRICING" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')" "$PRICING_PCT"
echo ""

# Process Status
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔄 RUNNING PROCESSES${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Check extended enrichment process
EXT_PROCESS=$(ps aux | grep "[e]nrich_cards_from_tcgdex.py")
if [ -n "$EXT_PROCESS" ]; then
    EXT_PID=$(echo "$EXT_PROCESS" | awk '{print $2}')
    EXT_CPU=$(echo "$EXT_PROCESS" | awk '{print $3}')
    EXT_MEM=$(echo "$EXT_PROCESS" | awk '{print $4}')
    echo -e "${GREEN}✓${NC} Extended Enrichment Process"
    printf "  %-20s PID %s (CPU: %s%%, MEM: %s%%)\n" "Status:" "$EXT_PID" "$EXT_CPU" "$EXT_MEM"
    if [ -n "$LATEST_EXT_NAME" ]; then
        printf "  %-20s #%s - %s\n" "Latest Card:" "$LATEST_EXT_ID" "$LATEST_EXT_NAME"
        printf "  %-20s %s\n" "TCGdex ID:" "$LATEST_EXT_TCGDEX"
    fi
    
    # Get last log entry
    if [ -f "enrichment_en.log" ]; then
        LAST_LOG=$(tail -1 enrichment_en.log | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('timestamp', 'N/A')[:19])" 2>/dev/null || echo "N/A")
        printf "  %-20s %s\n" "Last Activity:" "$LAST_LOG"
    fi
else
    echo -e "${YELLOW}✗${NC} Extended Enrichment Process: Not Running"
fi

echo ""

# Check pricing process
PRICE_PROCESS=$(ps aux | grep "[e]nrich_pricing_from_tcgdex.py")
if [ -n "$PRICE_PROCESS" ]; then
    PRICE_PID=$(echo "$PRICE_PROCESS" | awk '{print $2}')
    PRICE_CPU=$(echo "$PRICE_PROCESS" | awk '{print $3}')
    PRICE_MEM=$(echo "$PRICE_PROCESS" | awk '{print $4}')
    echo -e "${GREEN}✓${NC} Pricing Enrichment Process"
    printf "  %-20s PID %s (CPU: %s%%, MEM: %s%%)\n" "Status:" "$PRICE_PID" "$PRICE_CPU" "$PRICE_MEM"
    if [ -n "$LATEST_PRICE_NAME" ]; then
        printf "  %-20s #%s - %s\n" "Latest Card:" "$LATEST_PRICE_ID" "$LATEST_PRICE_NAME"
        printf "  %-20s %s\n" "TCGdex ID:" "$LATEST_PRICE_TCGDEX"
    fi
    
    # Get last log entry
    if [ -f "pricing_enrichment.log" ]; then
        LAST_LOG=$(tail -1 pricing_enrichment.log | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('timestamp', 'N/A')[:19])" 2>/dev/null || echo "N/A")
        printf "  %-20s %s\n" "Last Activity:" "$LAST_LOG"
    fi
else
    echo -e "${YELLOW}✗${NC} Pricing Enrichment Process: Not Running"
fi

echo ""

# Progress Bars
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}📈 PROGRESS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

# Function to draw progress bar
draw_progress_bar() {
    local current=$1
    local total=$2
    local label=$3
    local width=40
    local percentage=$(echo "scale=1; $current * 100 / $total" | bc)
    local filled=$(echo "scale=0; $current * $width / $total" | bc)
    
    printf "%-20s [" "$label"
    for ((i=0; i<width; i++)); do
        if [ $i -lt $filled ]; then
            printf "█"
        else
            printf "░"
        fi
    done
    printf "] %6.1f%% (%s/%s)\n" "$percentage" "$(printf '%s' "$current" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')" "$(printf '%s' "$total" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')"
}

draw_progress_bar "$EXTENDED" "$TOTAL" "Extended Data:"
draw_progress_bar "$PRICING" "$TOTAL" "Pricing Data:"

echo ""

# Estimates
if [ -n "$EXT_PROCESS" ] && [ "$EXTENDED" -lt "$TOTAL" ]; then
    REMAINING=$((TOTAL - EXTENDED))
    # Estimate 3 cards per second = 0.33s per card
    ETA_SECONDS=$(echo "scale=0; $REMAINING * 0.33" | bc)
    ETA_HOURS=$(echo "scale=1; $ETA_SECONDS / 3600" | bc)
    echo -e "${YELLOW}⏱  Extended Enrichment ETA: ~${ETA_HOURS} hours (${REMAINING} cards remaining)${NC}"
fi

if [ -n "$PRICE_PROCESS" ] && [ "$PRICING" -lt "$TOTAL" ]; then
    REMAINING=$((TOTAL - PRICING))
    # Estimate 0.5s per card
    ETA_SECONDS=$(echo "scale=0; $REMAINING * 0.5" | bc)
    ETA_HOURS=$(echo "scale=1; $ETA_SECONDS / 3600" | bc)
    echo -e "${YELLOW}⏱  Pricing Enrichment ETA: ~${ETA_HOURS} hours (${REMAINING} cards remaining)${NC}"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}💡 Commands:${NC}"
echo -e "  ${GREEN}./monitor_enrichment_status.sh${NC}     - Run this script again"
echo -e "  ${GREEN}tail -f enrichment_en.log${NC}          - Watch extended enrichment log"
echo -e "  ${GREEN}tail -f pricing_enrichment.log${NC}     - Watch pricing enrichment log"
echo -e "  ${GREEN}kill <PID>${NC}                         - Stop a process"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
