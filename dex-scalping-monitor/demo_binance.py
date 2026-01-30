#!/usr/bin/env python3
"""
DEX Scalping Monitor usando Binance API (gratuita, sin registro necesario)
Versión DEMO - Sin interacción
"""
import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import csv
import os

@dataclass
class Opportunity:
    pair: str
    price_change_pct: float
    roi_potential: float
    timestamp: str
    recommendation: str
    current_price: float
    volume_24h: float

class BinanceDexMonitor:
    """Monitor de DEX usando API pública de Binance"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    def __init__(self, price_threshold: float = 2.0, min_roi: float = 5.0):
        self.price_threshold = price_threshold
        self.min_roi = min_roi
        self.price_history: Dict[str, List[float]] = {}
        self.opportunities: List[Opportunity] = []
        os.makedirs("data", exist_ok=True)
        
    def get_all_tickers(self) -> Dict[str, dict]:
        """Obtiene todos los precios actuales"""
        try:
            print("📡 Consultando API de Binance...")
            response = requests.get(f"{self.BASE_URL}/ticker/24hr", timeout=15)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Datos recibidos: {len(data)} pares")
            return {item['symbol']: item for item in data}
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def scan_for_opportunities(self):
        """Escanea pares buscando oportunidades"""
        print("\n" + "="*80)
        print("🚀 DEX SCALPING MONITOR - Binance API (DEMO)")
        print("="*80)
        print(f"📊 Umbral: {self.price_threshold}% | ROI mínimo: {self.min_roi}%")
        print("="*80)
        
        # Obtener datos iniciales
        tickers = self.get_all_tickers()
        if not tickers:
            print("❌ No se pudieron obtener datos")
            return
        
        # Seleccionar pares TOP por volumen - ALTCOINS (incluyendo menores)
        print("\n📈 Analizando altcoins por volumen...")
        top_pairs = []
        for symbol, data in tickers.items():
            if symbol.endswith('USDT') and not symbol.startswith('USD'):
                try:
                    volume = float(data['quoteVolume'])
                    # Incluir altcoins con $500K+ de volumen (mucho más permisivo)
                    if volume > 500_000:
                        # Excluir stablecoins
                        if symbol not in ['USDTUSDT', 'BUSDUSDT', 'USDCUSDT', 'DAIUSDT', 'TUSDUSDT', 'FDUSDUSDT']:
                            top_pairs.append((symbol, volume, data))
                except:
                    continue
        
        top_pairs.sort(key=lambda x: x[1], reverse=True)
        # Tomar top 300 (o todos si hay menos)
        top_pairs = top_pairs[:300]
        
        print(f"✅ Analizando {len(top_pairs)} altcoins\n")
        
        # Mostrar solo los primeros 10 y los últimos 5 como muestra
        print("📊 Muestra de altcoins seleccionados:")
        for i, (symbol, volume, data) in enumerate(top_pairs[:10]):
            price = float(data['lastPrice'])
            self.price_history[symbol] = price
            print(f"  📌 {symbol}: ${price:,.6f} (Vol: ${volume/1e6:.2f}M)")
        
        if len(top_pairs) > 10:
            print(f"  ... y {len(top_pairs) - 10} altcoins más ...")
            # Mostrar los últimos 5
            for symbol, volume, data in top_pairs[-5:]:
                price = float(data['lastPrice'])
                self.price_history[symbol] = price
                print(f"  📌 {symbol}: ${price:,.6f} (Vol: ${volume/1e6:.2f}M)")
        
        # Guardar precios iniciales para todos
        for symbol, volume, data in top_pairs:
            if symbol not in self.price_history:
                price = float(data['lastPrice'])
                self.price_history[symbol] = price
        
        print("\n⏳ Esperando 30 segundos para comparar...")
        time.sleep(30)
        
        # Segunda consulta
        print("\n📡 Segunda consulta...")
        tickers = self.get_all_tickers()
        
        opportunities_found = []
        
        print("\n" + "="*80)
        print("🔍 ANALIZANDO MOVIMIENTOS...")
        print("="*80)
        
        for symbol, old_price in self.price_history.items():
            if symbol not in tickers:
                continue
                
            data = tickers[symbol]
            current_price = float(data['lastPrice'])
            volume_24h = float(data['quoteVolume'])
            
            # Calcular cambio
            change_pct = ((current_price - old_price) / old_price) * 100
            
            # Verificar si hay oportunidad
            if abs(change_pct) >= self.price_threshold:
                # Simular ROI potencial
                estimated_roi = abs(change_pct) * 0.7  # 70% del movimiento (menos fees)
                
                if change_pct > 0:
                    rec = f"🟢 CAIDA ESPERADA tras subida de +{change_pct:.2f}%"
                else:
                    rec = f"🟡 REBOTE POSIBLE tras bajada de {change_pct:.2f}%"
                
                opp = Opportunity(
                    pair=symbol,
                    price_change_pct=change_pct,
                    roi_potential=estimated_roi,
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    recommendation=rec,
                    current_price=current_price,
                    volume_24h=volume_24h
                )
                opportunities_found.append(opp)
                self._display_opportunity(opp)
        
        if not opportunities_found:
            print("\n⏳ No se detectaron oportunidades en este período")
            print("   (Esto es normal, el mercado puede estar estable)")
        else:
            print(f"\n🎯 {len(opportunities_found)} oportunidades detectadas")
            self._save_opportunities(opportunities_found)
        
        # Mostrar resumen
        print("\n" + "="*80)
        print("📊 RESUMEN DEL ANÁLISIS")
        print("="*80)
        print(f"Pares monitoreados: {len(top_pairs)}")
        print(f"Oportunidades encontradas: {len(opportunities_found)}")
        if opportunities_found:
            avg_roi = sum(o.roi_potential for o in opportunities_found) / len(opportunities_found)
            print(f"ROI promedio: {avg_roi:.2f}%")
        print(f"Datos guardados en: data/opportunities_demo.csv")
        print("="*80)
    
    def _display_opportunity(self, opp: Opportunity):
        """Muestra oportunidad"""
        print("\n" + "🔥"*40)
        print(f"🎯 OPORTUNIDAD: {opp.pair}")
        print(f"💰 Precio: ${opp.current_price:,.6f}")
        print(f"📈 Cambio: {opp.price_change_pct:+.2f}% (en 30s)")
        print(f"🎯 ROI estimado: {opp.roi_potential:.2f}%")
        print(f"📊 Volumen 24h: ${opp.volume_24h/1e6:.1f}M")
        print(f"⏰ {opp.timestamp}")
        print(f"📋 {opp.recommendation}")
        print("🔥"*40)
    
    def _save_opportunities(self, opportunities: List[Opportunity]):
        """Guarda en CSV"""
        filename = "data/opportunities_demo.csv"
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'pair', 'price', 'change_pct', 'roi_potential', 'volume_24h', 'recommendation'])
            
            for opp in opportunities:
                writer.writerow([
                    opp.timestamp, opp.pair, opp.current_price,
                    opp.price_change_pct, opp.roi_potential,
                    opp.volume_24h, opp.recommendation
                ])

def main():
    """Demo automático"""
    print("\n" + "="*80)
    print("  🚀 DEX SCALPING MONITOR - DEMO AUTOMÁTICA")
    print("  Usando Binance API Pública (Gratuita)")
    print("="*80)
    
    # Configuración fija para demo
    monitor = BinanceDexMonitor(price_threshold=1.5, min_roi=3.0)
    
    try:
        monitor.scan_for_opportunities()
    except KeyboardInterrupt:
        print("\n\n⚠️  Detenido")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
