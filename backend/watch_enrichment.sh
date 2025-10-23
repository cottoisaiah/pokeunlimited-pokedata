#!/bin/bash
# Continuous monitoring of both enrichment processes
# Press Ctrl+C to stop

cd /home/ubuntu/opt/app/pokeunlimited-pokedata/backend

while true; do
    ./monitor_enrichment_status.sh
    echo ""
    echo "🔄 Refreshing in 30 seconds... (Press Ctrl+C to stop)"
    sleep 30
done
