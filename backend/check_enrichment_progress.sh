#!/bin/bash
# Monitor card enrichment progress

echo "🎴 TCGdex Card Enrichment Progress Monitor"
echo "=========================================="
echo ""

# Database connection
DB="tradingcards"
USER="trading"

# Get total cards
TOTAL=$(PGPASSWORD=trading psql -U $USER -d $DB -t -c "SELECT COUNT(*) FROM pokedata_cards_en;")
echo "Total cards: $TOTAL"

# Get enriched cards (where category is not empty)
ENRICHED=$(PGPASSWORD=trading psql -U $USER -d $DB -t -c "SELECT COUNT(*) FROM pokedata_cards_en WHERE category != '' AND category IS NOT NULL;")
echo "Enriched cards: $ENRICHED"

# Calculate percentage
if [ $TOTAL -gt 0 ]; then
    PERCENT=$(echo "scale=2; ($ENRICHED * 100) / $TOTAL" | bc)
    echo "Progress: $PERCENT%"
fi

# Get recent enriched cards
echo ""
echo "Recent enrichments:"
PGPASSWORD=trading psql -U $USER -d $DB -c "SELECT id, name, category, rarity, hp, types FROM pokedata_cards_en WHERE category != '' AND category IS NOT NULL ORDER BY id DESC LIMIT 5;"

# Tail the log file
echo ""
echo "Recent log entries:"
tail -10 /home/ubuntu/opt/app/pokeunlimited-pokedata/backend/enrichment_en.log | grep -E "Card enriched|Batch complete|processed"
