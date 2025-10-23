#!/bin/bash
# Enrich all languages EXCEPT English (which is already running)

SCRIPT_DIR="/home/ubuntu/opt/app/pokeunlimited-pokedata/backend"
LOG_DIR="/home/ubuntu/opt/app/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# All languages EXCEPT English (already running)
LANGUAGES=(
    "ja"  # Japanese
    "de"  # German
    "es"  # Spanish
    "fr"  # French
    "it"  # Italian
    "ko"  # Korean
    "nl"  # Dutch
    "pl"  # Polish
    "pt_br"  # Portuguese (Brazil)
    "ru"  # Russian
    "th"  # Thai
    "zh_cn"  # Chinese (Simplified)
    "zh_tw"  # Chinese (Traditional)
    "id"  # Indonesian
)

echo "🎴 Starting Card Data & Pricing Enrichment for Remaining Languages"
echo "=================================================================="
echo "Start time: $(date)"
echo "Note: English (en) is already running in background"
echo ""

for lang in "${LANGUAGES[@]}"; do
    echo ""
    echo "📦 Processing language: $lang"
    echo "----------------------------------------"
    
    # Step 1: Enrich card data
    echo "🔧 Step 1: Enriching card data for $lang..."
    cd "$SCRIPT_DIR"
    python3 enrich_cards_from_tcgdex.py \
        --lang "$lang" \
        --batch-size 100 \
        --delay 0.3 \
        2>&1 | tee "$LOG_DIR/enrich_data_${lang}_${TIMESTAMP}.log"
    
    DATA_EXIT_CODE=$?
    
    if [ $DATA_EXIT_CODE -eq 0 ]; then
        echo "✅ Data enrichment completed for $lang"
        
        # Step 2: Enrich pricing (only for enriched cards)
        echo "💰 Step 2: Enriching pricing data for $lang..."
        python3 enrich_pricing_from_tcgdex.py \
            --lang "$lang" \
            --batch-size 100 \
            --delay 0.3 \
            2>&1 | tee "$LOG_DIR/enrich_pricing_${lang}_${TIMESTAMP}.log"
        
        PRICING_EXIT_CODE=$?
        
        if [ $PRICING_EXIT_CODE -eq 0 ]; then
            echo "✅ Pricing enrichment completed for $lang"
        else
            echo "❌ Pricing enrichment failed for $lang (exit code: $PRICING_EXIT_CODE)"
        fi
    else
        echo "❌ Data enrichment failed for $lang (exit code: $DATA_EXIT_CODE)"
        echo "⏭️  Skipping pricing enrichment for $lang"
    fi
    
    echo "----------------------------------------"
done

echo ""
echo "=================================================================="
echo "🎉 All remaining languages processed!"
echo "End time: $(date)"
echo ""
echo "📊 Check logs in: $LOG_DIR"
echo ""
echo "💡 Don't forget to check English enrichment status (still running in background)"
