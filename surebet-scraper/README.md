# SureBet Scraper - Arbitrage Betting Detector

Scraper de oportunidades de arbitrage (surebets) para casas de apuestas argentinas.

## Características

- Scrapea odds de BetWarrior, Codere, Bplay y Betsson
- Detecta automáticamente oportunidades de surebet
- Calcula stake óptimo usando distribución proporcional
- Muestra ROI esperado
- Guarda datos en CSV y JSON
- Soporta Liga Profesional Argentina y principales ligas europeas

## Requisitos

- Python 3.8+
- Chrome/Chromium instalado (para scraping real)

## Instalación

```bash
# Clonar o descargar el proyecto
cd surebet-scraper

# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar Playwright browsers (solo si vas a hacer scraping real)
playwright install chromium
```

## Uso

### Modo Demo (sin dependencias)

Para probar el sistema sin necesidad de instalar Playwright:

```bash
python surebet_scraper.py --demo
```

### Ejecución básica (scraping real)

```bash
python surebet_scraper.py
```

### Opciones disponibles

```bash
python surebet_scraper.py --help

# Modo demo con datos de ejemplo
python surebet_scraper.py --demo

# Escanear solo ligas específicas
python surebet_scraper.py --ligas "Primera Division,La Liga,Premier League"

# Ajustar margen mínimo de surebet (default: 1.0%)
python surebet_scraper.py --margen 0.5

# Especificar stake total disponible (default: $10000 ARS)
python surebet_scraper.py --stake 50000

# Modo headless (sin abrir navegador)
python surebet_scraper.py --headless

# Exportar solo JSON o solo CSV
python surebet_scraper.py --format json
```

## Configuración

Edita `config.py` para personalizar:
- URLs de las casas de apuestas
- Ligas a monitorear
- Umbrales de margen
- Límites de stake

## Cómo Funciona

### Detección de Surebets

Una surebet (arbitrage) ocurre cuando las odds de diferentes casas de apuestas permiten apostar a todos los resultados de un evento y obtener ganancia garantizada.

**Fórmula de detección:**
```
Si Σ(1 / mejor_odd_para_cada_resultado) < 1 → Hay surebet
```

**Ejemplo:**
- Local: BetWarrior @ 2.50
- Empate: Codere @ 3.60  
- Visitante: Bplay @ 3.30

```
1/2.50 + 1/3.60 + 1/3.30 = 0.40 + 0.278 + 0.303 = 0.981 < 1 ✓
```

**Margen:** (1 - 0.981) × 100 = **1.92%**

### Cálculo de Stakes

Usamos distribución proporcional (método más simple y efectivo):

```python
stake_i = (total_stake / odds_i) / Σ(1/odds) × total_stake
```

Esto garantiza el mismo retorno sin importa el resultado.

## Salida

Los resultados se guardan en:
- `data/odds_YYYYMMDD_HHMMSS.csv` - Todas las odds scrapeadas
- `data/surebets_YYYYMMDD_HHMMSS.json` - Oportunidades de surebet detectadas
- `data/surebets_YYYYMMDD_HHMMSS.csv` - Surebets en formato tabla

## Ejemplo de Salida

### Consola
```
============================================================
🎯 OPORTUNIDAD SUREBET DETECTADA
============================================================

📅 Partido: Boca Juniors vs River Plate
🏆 Liga: Primera Division
📊 Mercado: 1X2

💰 Distribución óptima (Stake total: $10,000.00):
--------------------------------------------------
  • Local (BetWarrior):
      Odds: 2.5 | Stake: $4,078.27 | Retorno: $10,195.67
  • Empate (Codere):
      Odds: 3.6 | Stake: $2,832.13 | Retorno: $10,195.67
  • Visitante (Bplay):
      Odds: 3.3 | Stake: $3,089.60 | Retorno: $10,195.67

📈 Resultado:
  • Margen: 1.92%
  • ROI: 1.96%
  • Ganancia garantizada: $195.67
============================================================
```

### JSON
```json
{
  "match": {
    "home_team": "Boca Juniors",
    "away_team": "River Plate",
    "league": "Primera Division"
  },
  "market": "1X2",
  "margin": 1.92,
  "roi": 1.96,
  "stakes": [
    {"outcome": "1", "bookmaker": "BetWarrior", "odds": 2.5, "stake": 4078.27},
    {"outcome": "X", "bookmaker": "Codere", "odds": 3.6, "stake": 2832.13},
    {"outcome": "2", "bookmaker": "Bplay", "odds": 3.3, "stake": 3089.60}
  ],
  "guaranteed_profit": 195.67
}
```

## Estructura del Proyecto

```
surebet-scraper/
├── surebet_scraper.py    # Script principal
├── config.py              # Configuración
├── requirements.txt       # Dependencias
├── README.md             # Documentación
├── run.sh                # Script de ejecución
├── example_output.txt    # Ejemplo de salida
└── data/                 # Archivos generados
    ├── odds_*.csv
    ├── surebets_*.json
    └── surebets_*.csv
```

## Implementación de Scraping Real

⚠️ **Nota importante:** El script actual incluye una implementación de ejemplo/simulación. Para scraping real de las casas de apuestas:

1. Las casas de apuestas cambian frecuentemente sus sitios web
2. Es posible que necesites actualizar los selectores CSS en `config.py`
3. Algunas casas tienen protecciones anti-scraping (CAPTCHAs, rate limiting)
4. Se recomienda usar proxies rotativos para evitar bloqueos
5. Las odds cambian en tiempo real; el scraping debe ser rápido

### Para desarrolladores:

Para implementar scraping real, modifica el método `_extract_matches()` en la clase `BookmakerScraper`:

```python
async def _extract_matches(self, league_filter=None):
    # Parsear el HTML usando BeautifulSoup o los selectores de Playwright
    content = await self.page.content()
    soup = BeautifulSoup(content, 'html.parser')
    
    # Extraer datos según los selectores de config.py
    events = soup.select(self.selectors['event_container'])
    
    for event in events:
        # Extraer información del partido
        teams = event.select(self.selectors['team_names'])
        odds = event.select(self.selectors['odds'])
        
        # Crear objetos Match y Odd
        # ...
```

## Advertencias Legales y de Uso

⚠️ **IMPORTANTE:**
- Este script es solo para fines informativos y educativos
- Las casas de apuestas pueden modificar sus términos o prohibir el arbitrage
- Verifica la legalidad del gambling en tu jurisdicción
- No nos hacemos responsables por pérdidas financieras
- El usuario es responsable de verificar las odds antes de apostar
- El arbitrage betting puede resultar en limitaciones de cuenta por parte de las casas

## Limitaciones Conocidas

- Las casas de apuestas pueden bloquear scraping con CAPTCHAs
- Las odds cambian rápidamente; la información puede quedar desactualizada
- Algunas casas requieren VPN para acceso desde ciertas ubicaciones
- Los límites de stake varían según el usuario y la casa
- Los palps/errores de las casas pueden generar falsas surebets

## Contribuciones

Las contribuciones son bienvenidas. Por favor, mantén el código enfocado solo en scraping, no en automatización de apuestas.

## Licencia

MIT License - Uso educativo únicamente.
