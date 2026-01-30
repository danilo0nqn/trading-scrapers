#!/bin/bash
# Script para ejecutar el SureBet Scraper fácilmente

cd "$(dirname "$0")"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ejecutar con opciones por defecto o las proporcionadas
python3 surebet_scraper.py "$@"
