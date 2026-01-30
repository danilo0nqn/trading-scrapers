# 🚀 DEX Scalping Monitor - Notebook Setup

Monitor de oportunidades de scalping en criptomonedas para correr 24/7 en tu notebook.

## 📥 Instalación Rápida

### 1. Descargar el repo
```bash
git clone https://github.com/danilo0nqn/trading-scrapers.git
cd trading-scrapers/dex-scalping-monitor
```

### 2. Crear archivo .env
Crear archivo `.env` en esta carpeta con el siguiente contenido:

```env
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
```

### 3. Instalar dependencias
```bash
# Windows
python -m pip install requests

# Mac/Linux
pip3 install requests
```

### 4. Ejecutar
```bash
# Windows
python demo_binance.py

# Mac/Linux  
python3 demo_binance.py
```

## 🔄 Correr 24/7

### Opción A: Dejar corriendo en terminal
```bash
# Windows - usar git bash o PowerShell
while ($true) { python demo_binance.py; Start-Sleep -Seconds 60 }

# Linux/Mac
while true; do python3 demo_binance.py; sleep 60; done
```

### Opción B: Usar PM2 (recomendado)
```bash
# Instalar PM2
npm install -g pm2

# Iniciar monitor
pm2 start demo_binance.py --name "dex-monitor" --interpreter python3

# Ver logs
pm2 logs dex-monitor

# Detener
pm2 stop dex-monitor
```

### Opción C: Systemd (Linux)
```bash
sudo nano /etc/systemd/system/dex-monitor.service
```

Contenido:
```ini
[Unit]
Description=DEX Scalping Monitor
After=network.target

[Service]
Type=simple
User=tu-usuario
WorkingDirectory=/ruta/al/proyecto/dex-scalping-monitor
ExecStart=/usr/bin/python3 demo_binance.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar:
```bash
sudo systemctl enable dex-monitor
sudo systemctl start dex-monitor
sudo systemctl status dex-monitor
```

## 📊 Ver resultados

Los resultados se guardan en:
- `data/opportunities_demo.csv` - Histórico de oportunidades
- `data/opportunities_history.csv` - Histórico extendido

## 🔧 Configuración

Editar `.env` para ajustar:
- `PRICE_CHANGE_THRESHOLD` - % de cambio para alerta (default: 3%)
- `MIN_ROI_THRESHOLD` - ROI mínimo para mostrar (default: 10%)
- `MONITOR_INTERVAL` - Segundos entre chequeos (default: 60)

## 🌐 Acceso remoto

Para que yo pueda acceder desde el Raspberry Pi:

### Opción 1: SSH (más seguro)
```bash
# En tu notebook, instalar OpenSSH
# Windows: Configuración > Apps > OpenSSH Server
# Mac: System Preferences > Sharing > Remote Login
# Linux: sudo apt install openssh-server

# Verificar IP
ipconfig  # Windows
ifconfig  # Mac/Linux
```

### Opción 2: TeamViewer / AnyDesk
Instalar y darme el ID/contraseña.

### Opción 3: VS Code Server
```bash
# Instalar code-server
curl -fsSL https://code-server.dev/install.sh | sh

# Correr
code-server --bind-addr 0.0.0.0:8080
```

## 📱 Notificaciones (opcional)

Para recibir alertas en WhatsApp cuando haya oportunidades, agregar webhook o integrar con Twilio.

## ⚠️ Notas

- El monitor usa **API pública de Binance** (gratis, no necesita registro)
- El API key de Alchemy es opcional (solo para datos on-chain avanzados)
- No necesita GPU, corre en cualquier notebook
- Consume pocos recursos (<100MB RAM)

## 🆘 Soporte

Si hay problemas:
1. Verificar que Python 3.8+ esté instalado
2. Verificar conexión a internet
3. Revisar archivo `.env` esté creado
