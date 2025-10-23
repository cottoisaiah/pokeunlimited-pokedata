#!/bin/bash
# Monitor enrichment status across all languages

echo "🎴 Card Data Enrichment Status Monitor"
echo "======================================"
echo "Last updated: $(date)"
echo ""

# Check running processes
echo "📊 Running Enrichment Processes:"
echo "--------------------------------"
ps aux | grep python3 | grep enrich | grep -v grep | awk '{print "  PID: " $2 " | " $11 " " $12 " " $13 " " $14 " " $15}'
if [ $? -ne 0 ]; then
    echo "  No enrichment processes currently running"
fi
echo ""

# Check database status for each language
echo "📈 Database Enrichment Progress:"
echo "--------------------------------"

PGPASSWORD=trading psql -U trading -h localhost -d tradingcards -t << 'EOF'
SELECT 
    lang,
    total_cards,
    enriched_cards,
    ROUND(100.0 * enriched_cards / NULLIF(total_cards, 0), 1) || '%' as enrichment_pct,
    with_images,
    ROUND(100.0 * with_images / NULLIF(total_cards, 0), 1) || '%' as image_pct
FROM (
    SELECT 'en' as lang, COUNT(*) as total_cards, 
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_en
    UNION ALL
    SELECT 'ja' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_ja
    UNION ALL
    SELECT 'de' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_de
    UNION ALL
    SELECT 'es' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_es
    UNION ALL
    SELECT 'fr' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_fr
    UNION ALL
    SELECT 'it' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_it
    UNION ALL
    SELECT 'ko' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_ko
    UNION ALL
    SELECT 'nl' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_nl
    UNION ALL
    SELECT 'pl' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_pl
    UNION ALL
    SELECT 'pt_br' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_pt_br
    UNION ALL
    SELECT 'ru' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_ru
    UNION ALL
    SELECT 'th' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_th
    UNION ALL
    SELECT 'zh_cn' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_zh_cn
    UNION ALL
    SELECT 'zh_tw' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_zh_tw
    UNION ALL
    SELECT 'id' as lang, COUNT(*) as total_cards,
           COUNT(CASE WHEN category IS NOT NULL AND category != '' THEN 1 END) as enriched_cards,
           COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_images
    FROM pokedata_cards_id
) stats
ORDER BY lang;
EOF

echo ""
echo "======================================"
echo "💡 Usage: ./check_enrichment_status.sh"
echo "📝 Run this script periodically to monitor progress"
