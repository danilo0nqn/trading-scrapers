#!/bin/bash
# Script para correr el monitor 24/7 en la Raspberry Pi

cd /home/alfred/clawd/projects/dex-scalping-monitor

echo "========================================"
echo "🚀 Iniciando DEX Monitor 24/7"
echo "========================================"
echo "Presiona Ctrl+C para detener"
echo ""

while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Ejecutando monitor..."
    python3 demo_binance.py
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Esperando 2 minutos..."
    echo "----------------------------------------"
    sleep 120
done
