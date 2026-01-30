"""
DEX Scalping Monitor usando Binance API (gratuita, sin registro necesario)
"""
import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import csv
import os

@dataclass
class TokenPair:
    symbol: str
    base_asset: str
    quote_asset: str
    price: float
    price_1m_ago: float = 0.0
    volume_24h: float = 0.0
    price_change_1m: float = 0.0
    
@dataclass
class Opportunity:
    pair: str
    price_change_pct: float
    roi_potential: float
    timestamp: str
    recommendation: str

class BinanceDexMonitor:
    """Monitor de DEX usando API pública de Binance (gratuita)"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    # Pares populares para monitorear
    POPULAR_PAIRS = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
        "DOGEUSDT", "XRPUSDT", "DOTUSDT", "AVAXUSDT", "MATICUSDT",
        "LINKUSDT", "UNIUSDT", "AAVEUSDT", "SUSHIUSDT", "1INCHUSDT",
        "PEPEUSDT", "SHIBUSDT", "FLOKIUSDT", "BONKUSDT", "WIFUSDT"
    ]
    
    def __init__(self, price_threshold: float = 3.0, min_roi: float = 5.0):
        self.price_threshold = price_threshold  # % cambio para alerta
        self.min_roi = min_roi  # % ROI mínimo
        self.price_history: Dict[str, List[float]] = {}
        self.opportunities: List[Opportunity] = []
        
        # Crear directorio de datos
        os.makedirs("data", exist_ok=True)
        
    def get_all_tickers(self) -> Dict[str, dict]:
        """Obtiene todos los precios actuales"""
        try:
            response = requests.get(f"{self.BASE_URL}/ticker/24hr", timeout=10)
            response.raise_for_status()
            data = response.json()
            return {item['symbol']: item for item in data}
        except Exception as e:
            print(f"❌ Error obteniendo tickers: {e}")
            return {}
    
    def get_top_volume_pairs(self, limit: int = 30) -> List[str]:
        """Obtiene los pares con mayor volumen"""
        tickers = self.get_all_tickers()
        
        # Filtrar solo los pares que nos interesan y tienen buen volumen
        valid_pairs = []
        for symbol, data in tickers.items():
            if symbol.endswith('USDT'):
                try:
                    volume = float(data['volume'])
                    price = float(data['lastPrice'])
                    quote_volume = volume * price
                    
                    # Mínimo $10M de volumen diario
                    if quote_volume > 10_000_000:
                        valid_pairs.append((symbol, quote_volume))
                except:
                    continue
        
        # Ordenar por volumen y tomar los top
        valid_pairs.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in valid_pairs[:limit]]
    
    def monitor_pairs(self, duration_minutes: int = 5):
        """Monitorea pares durante X minutos buscando oportunidades"""
        print("=" * 80)
        print("🚀 DEX SCALPING MONITOR - Binance API")
        print("=" * 80)
        print(f"⏱️  Duración: {duration_minutes} minutos")
        print(f"📊 Umbral de cambio: {self.price_threshold}%")
        print(f"💰 ROI mínimo: {self.min_roi}%")
        print("=" * 80)
        
        # Obtener pares iniciales
        print("\n📈 Obteniendo pares de alto volumen...")
        pairs = self.get_top_volume_pairs(20)
        print(f"✅ Monitoreando {len(pairs)} pares\n")
        
        # Precios iniciales
        print("💾 Guardando precios iniciales...")
        tickers = self.get_all_tickers()
        for pair in pairs:
            if pair in tickers:
                price = float(tickers[pair]['lastPrice'])
                self.price_history[pair] = [price]
        
        print(f"⏳ Esperando 60 segundos para primera comparación...\n")
        
        start_time = time.time()
        check_count = 0
        
        while (time.time() - start_time) < (duration_minutes * 60):
            time.sleep(60)  # Chequear cada minuto
            check_count += 1
            
            print(f"\n{'='*80}")
            print(f"🔍 Chequeo #{check_count} - {datetime.now().strftime('%H:%M:%S')}")
            print('='*80)
            
            tickers = self.get_all_tickers()
            opportunities_found = []
            
            for pair in pairs:
                if pair not in tickers:
                    continue
                    
                current_price = float(tickers[pair]['lastPrice'])
                
                if pair not in self.price_history:
                    self.price_history[pair] = [current_price]
                    continue
                
                # Calcular cambio desde el último precio
                prev_price = self.price_history[pair][-1]
                price_change = ((current_price - prev_price) / prev_price) * 100
                
                # Calcular cambio desde el inicio
                start_price = self.price_history[pair][0]
                total_change = ((current_price - start_price) / start_price) * 100
                
                # Guardar en historial
                self.price_history[pair].append(current_price)
                if len(self.price_history[pair]) > 10:
                    self.price_history[pair].pop(0)
                
                # Detectar oportunidad
                if abs(price_change) >= self.price_threshold:
                    volume = float(tickers[pair]['volume'])
                    price_data = tickers[pair]
                    
                    opportunity = self._analyze_opportunity(
                        pair, current_price, prev_price, price_change, 
                        volume, price_data
                    )
                    
                    if opportunity:
                        opportunities_found.append(opportunity)
                        self._display_opportunity(opportunity)
            
            if not opportunities_found:
                print("⏳ No se encontraron oportunidades en este chequeo")
            else:
                print(f"\n🎯 {len(opportunities_found)} oportunidades encontradas")
                self._save_opportunities(opportunities_found)
        
        print("\n" + "="*80)
        print("✅ Monitoreo completado")
        print(f"📁 Oportunidades guardadas en: data/opportunities_binance.csv")
        print("="*80)
    
    def _analyze_opportunity(self, pair: str, current: float, previous: float, 
                            change: float, volume: float, data: dict) -> Optional[Opportunity]:
        """Analiza si es una oportunidad válida"""
        
        # Calcular spread
        bid = float(data.get('bidPrice', current * 0.999))
        ask = float(data.get('askPrice', current * 1.001))
        spread = ((ask - bid) / current) * 100
        
        # Estimar ROI (simplificado)
        # Asumimos: 0.1% fee por trade (0.2% total ida y vuelta)
        fees = 0.2
        potential_profit = abs(change) - fees
        
        # Liquidez mínima (quote volume > $1M)
        quote_volume = volume * current
        if quote_volume < 1_000_000:
            return None
        
        # Determinar recomendación
        if change > 0 and potential_profit > self.min_roi:
            rec = f"🟢 SHORT: Bajada esperada tras subida de {change:.2f}%"
            roi = potential_profit
        elif change < 0 and potential_profit > self.min_roi:
            rec = f"🟡 LONG: Posible rebote tras bajada de {change:.2f}%"
            roi = potential_profit
        else:
            return None
        
        return Opportunity(
            pair=pair,
            price_change_pct=change,
            roi_potential=roi,
            timestamp=datetime.now().isoformat(),
            recommendation=rec
        )
    
    def _display_opportunity(self, opp: Opportunity):
        """Muestra una oportunidad en pantalla"""
        print("\n" + "🔥"*40)
        print(f"🎯 OPORTUNIDAD DETECTADA: {opp.pair}")
        print("🔥"*40)
        print(f"📊 Cambio de precio: {opp.price_change_pct:+.2f}%")
        print(f"💰 ROI potencial: {opp.roi_potential:.2f}%")
        print(f"⏰ Timestamp: {opp.timestamp}")
        print(f"📋 {opp.recommendation}")
        print("🔥"*40)
    
    def _save_opportunities(self, opportunities: List[Opportunity]):
        """Guarda oportunidades en CSV"""
        filename = "data/opportunities_binance.csv"
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['pair', 'price_change_pct', 'roi_potential', 'timestamp', 'recommendation'])
            
            for opp in opportunities:
                writer.writerow([
                    opp.pair, 
                    opp.price_change_pct, 
                    opp.roi_potential, 
                    opp.timestamp, 
                    opp.recommendation
                ])


def main():
    """Ejecuta el monitor"""
    print("\n" + "="*80)
    print("  DEX SCALPING MONITOR - Binance Edition")
    print("  Sin registro necesario - API Pública")
    print("="*80 + "\n")
    
    # Configuración
    threshold = float(input("Umbral de cambio de precio [%] (default 3): ") or "3")
    min_roi = float(input("ROI mínimo [%] (default 5): ") or "5")
    duration = int(input("Duración del monitoreo [min] (default 5): ") or "5")
    
    # Iniciar monitor
    monitor = BinanceDexMonitor(
        price_threshold=threshold,
        min_roi=min_roi
    )
    
    try:
        monitor.monitor_pairs(duration_minutes=duration)
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoreo interrumpido por usuario")


if __name__ == "__main__":
    main()
