#!/bin/bash
# Script de instalación automática para DEX Scalping Monitor
# Compatible: Linux, Mac, Windows (Git Bash)

echo "=========================================="
echo "🚀 DEX Scalping Monitor - Instalador"
echo "=========================================="

# Detectar OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="Mac"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="Windows"
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    OS="Unknown"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

echo "📱 Sistema detectado: $OS"

# Verificar Python
echo "🔍 Verificando Python..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python no encontrado. Por favor instalar Python 3.8+ desde https://python.org"
    exit 1
fi

echo "✅ Python encontrado: $($PYTHON_CMD --version)"

# Instalar dependencias
echo "📦 Instalando dependencias..."
$PIP_CMD install requests python-dotenv

# Crear .env si no existe
if [ ! -f ".env" ]; then
    echo "📝 Creando archivo .env..."
    cat > .env << 'EOF'
# Configuración para DEX Scalping Monitor
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/6kBHIebPq9u0fcqQUPWdP
BSC_RPC_URL=https://bsc-dataseed.binance.org/

# Umbrales de alerta
PRICE_CHANGE_THRESHOLD=3.0
MIN_ROI_THRESHOLD=10.0
MONITOR_INTERVAL=60

# Configuración de trade
TRADE_AMOUNT_USD=100.0
MAX_GAS_PRICE_GWEI=50

# Alertas
ENABLE_SOUND_ALERTS=true
ENABLE_CONSOLE_ALERTS=true
ALERT_COOLDOWN=300
EOF
    echo "✅ Archivo .env creado"
else
    echo "✅ Archivo .env ya existe"
fi

# Crear directorio de datos
mkdir -p data

# Probar ejecución
echo "🧪 Probando instalación..."
$PYTHON_CMD -c "import requests; print('✅ requests OK')"

echo ""
echo "=========================================="
echo "✅ Instalación completada!"
echo "=========================================="
echo ""
echo "Para ejecutar el monitor:"
echo "  $PYTHON_CMD demo_binance.py"
echo ""
echo "Para correr 24/7:"
echo "  $PYTHON_CMD binance_monitor.py"
echo ""
echo "Para más opciones ver SETUP_NOTEBOOK.md"
echo "=========================================="
