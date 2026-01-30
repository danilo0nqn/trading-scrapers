# 🚀 DEX Scalping Monitor

Monitor de oportunidades de scalping para altcoins en exchanges descentralizados (DEX). Detecta movimientos bruscos de precio en tiempo real y calcula ROI potencial considerando gas fees.

## ✨ Características

- **🔌 Multi-DEX Support**: Uniswap V3 (Ethereum) y PancakeSwap (BSC)
- **⚡ Monitoreo en Tiempo Real**: Detecta movimientos >5% en 1 minuto
- **💰 Cálculo de ROI**: Considera gas fees vs ganancia potencial
- **🚨 Alertas Inteligentes**: Notifica cuando ROI > 10% después de fees
- **📊 Histórico de Oportunidades**: Guarda datos en CSV para análisis
- **🎨 Interfaz Colorida**: Fácil lectura con colores y tablas

## 📋 Requisitos

- Python 3.8+
- API Key de Alchemy, Infura, o RPC público
- Conexión a Internet estable

## 🚀 Instalación

### 1. Clonar o crear el proyecto

```bash
cd /home/alfred/clawd/projects/dex-scalping-monitor
```

### 2. Probar en Modo Demo (Sin dependencias)

Para ver cómo funciona el monitor sin necesidad de instalar dependencias ni configurar API keys:

```bash
python3 demo.py
```

Esto ejecuta una simulación con datos aleatorios mostrando cómo se verían las alertas y oportunidades.

### 3. Crear entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar API Keys

```bash
cp .env.example .env
# Editar .env con tu editor favorito
nano .env  # o vim, code, etc.
```

Edita el archivo `.env` y añade tus API keys:

```env
# Ethereum (Uniswap V3) - Obtén tu API key en https://www.alchemy.com
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/TU_API_KEY_AQUI

# BSC (PancakeSwap) - Puedes usar el RPC público o QuickNode
BSC_RPC_URL=https://bsc-dataseed.binance.org/
```

### 6. Ejecutar

**Demo Simple** (sin dependencias, solo para ver interfaz):
```bash
python3 demo.py
```

**Modo Demo** (con dependencias, sin conexión blockchain):
```bash
python dex_monitor.py --demo
```

**Modo Real** (con conexión blockchain):
```bash
python dex_monitor.py
```

## ⚙️ Configuración

Edita el archivo `.env` para personalizar:

| Variable | Descripción | Default |
|----------|-------------|---------|
| `PRICE_CHANGE_THRESHOLD` | Umbral de cambio de precio para alerta (%) | 5.0 |
| `MIN_ROI_THRESHOLD` | ROI mínimo para considerar viable (%) | 10.0 |
| `MONITOR_INTERVAL` | Intervalo de monitoreo (segundos) | 60 |
| `MAX_GAS_PRICE_GWEI` | Precio máximo de gas aceptable (Gwei) | 100 |
| `TRADE_AMOUNT_USD` | Monto de trade para cálculo ROI (USD) | 1000 |
| `ALERT_COOLDOWN` | Tiempo entre alertas del mismo par (segundos) | 300 |

## 📊 Métricas Monitoreadas

Para cada par de tokens, el monitor muestra:

- **Token Pair**: Par de tokens (ej: PEPE/WETH)
- **Cambio de Precio (1m)**: Variación porcentual en 1 minuto
- **Volumen 24h**: Volumen de trading estimado
- **Liquidez**: Liquidez disponible en el pool
- **Gas Fee**: Costo estimado de gas en USD
- **ROI Potencial**: Retorno de inversión después de fees

## 🎯 Ejemplo de Salida

```
================================================================================
  DEX Scalping Monitor v1.0
  Monitoring Uniswap V3 & PancakeSwap
================================================================================

✓ Ethereum connected (Chain ID: 1)
✓ BSC connected (Chain ID: 56)

Starting monitoring loop...
Price change threshold: 5.0%
Min ROI threshold: 10.0%
Monitoring interval: 60s

[2024-01-15 14:32:10] Scanning for opportunities...

+------------+-------------+------------+-----------+-------+-----------+
| Pair       | Change (1m) | Volume 24h | Gas Fee   | ROI   | Status    |
+============+=============+============+===========+=======+===========+
| WETH/USDC  | -2.3%       | $125M      | $12.50    | -1.2% |           |
| PEPE/WETH  | +8.5%       | $5M        | $15.00    | +7.0% |  ✓ VIABLE |
| SHIB/WETH  | -1.2%       | $8M        | $14.20    | -0.5% |           |
+------------+-------------+------------+-----------+-------+-----------+

================================================================================
🚨 SCALPING OPPORTUNITY DETECTED!
================================================================================
Pair: PEPE/WETH (uniswap)
Price Change: +8.5%
Volume 24h: $5,000,000
Liquidity: 2,500,000
Gas Fee: $15.00
Potential Profit: $85.00
ROI after fees: 7.0%
================================================================================
```

## 📁 Estructura del Proyecto

```
dex-scalping-monitor/
├── dex_monitor.py      # Script principal
├── config.py           # Configuración
├── requirements.txt    # Dependencias
├── .env.example        # Ejemplo de configuración
├── .env                # Tu configuración (no compartir)
├── README.md           # Este archivo
├── data/               # Histórico de oportunidades
│   └── opportunities_history.csv
└── logs/               # Logs de ejecución
    └── dex_monitor.log
```

## 🔑 Obtener API Keys

### Alchemy (Recomendado)
1. Ve a https://www.alchemy.com
2. Crea una cuenta gratuita
3. Crea una nueva app
4. Copia la URL del HTTP Provider
5. Pégala en tu archivo `.env`

### Infura (Alternativa)
1. Ve a https://infura.io
2. Crea una cuenta
3. Crea un nuevo proyecto Ethereum
4. Copia el endpoint

## ⚠️ Notas Importantes

- **Este es solo un monitor**: No ejecuta trades automáticamente
- **El usuario opera manualmente**: Las alertas son informativas
- **Gas fees variables**: Los cálculos son estimados, pueden variar
- **Slippage no considerado**: En producción real, considera slippage
- **Liquidez limitada**: Verifica la liquidez antes de operar

## 🔧 Troubleshooting

### Error: "Failed to connect to Ethereum"
- Verifica tu API key de Alchemy/Infura
- Comprueba tu conexión a Internet
- Asegúrate de que el RPC URL esté correcto

### Error: "No module named 'web3'"
```bash
pip install -r requirements.txt
```

### No se detectan oportunidades
- Ajusta `PRICE_CHANGE_THRESHOLD` a un valor menor
- Verifica que los pares estén cargando correctamente
- Revisa los logs en `logs/dex_monitor.log`

## 📈 Mejoras Futuras

- [ ] Integración con TheGraph para datos históricos
- [ ] Alertas por Telegram/Discord
- [ ] Dashboard web en tiempo real
- [ ] Soporte para más DEX (SushiSwap, Curve, etc.)
- [ ] Análisis técnico básico (RSI, MACD)
- [ ] Detección de pumps/dumps

## 📄 Licencia

MIT License - Uso libre para fines personales y comerciales.

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

---

**Disclaimer**: Este software es solo para fines educativos. El trading de criptomonedas conlleva riesgos significativos. Nunca inviertas más de lo que puedas permitirte perder.
