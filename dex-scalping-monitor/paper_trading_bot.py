#!/usr/bin/env python3
"""
Paper Trading Bot - Simulación con $100
Monitorea cada 2 minutos y simula operaciones
"""
import requests
import time
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import csv
import os

@dataclass
class Trade:
    timestamp: str
    pair: str
    action: str  # BUY o SELL
    price: float
    amount_usd: float
    quantity: float
    reason: str

@dataclass
class Portfolio:
    cash: float
    positions: Dict[str, float]  # pair -> quantity
    trade_history: List[Trade]
    total_trades: int
    winning_trades: int
    losing_trades: int
    
class PaperTradingBot:
    """Bot de paper trading para DEX/altcoins"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    def __init__(self, initial_cash: float = 100.0):
        self.initial_cash = initial_cash
        self.portfolio = Portfolio(
            cash=initial_cash,
            positions={},
            trade_history=[],
            total_trades=0,
            winning_trades=0,
            losing_trades=0
        )
        self.price_history: Dict[str, List[float]] = {}
        self.entry_prices: Dict[str, float] = {}  # Precio de entrada por posición
        
        os.makedirs("data/paper_trading", exist_ok=True)
        self.load_portfolio()
        
    def load_portfolio(self):
        """Carga portfolio guardado si existe"""
        try:
            with open("data/paper_trading/portfolio.json", "r") as f:
                data = json.load(f)
                self.portfolio.cash = data.get("cash", self.initial_cash)
                self.portfolio.positions = data.get("positions", {})
                self.portfolio.total_trades = data.get("total_trades", 0)
                self.portfolio.winning_trades = data.get("winning_trades", 0)
                self.portfolio.losing_trades = data.get("losing_trades", 0)
                self.entry_prices = data.get("entry_prices", {})
                print(f"📂 Portfolio cargado: ${self.portfolio.cash:.2f} cash")
        except:
            print(f"🆕 Nuevo portfolio creado: ${self.initial_cash}")
    
    def save_portfolio(self):
        """Guarda estado del portfolio"""
        data = {
            "cash": self.portfolio.cash,
            "positions": self.portfolio.positions,
            "total_trades": self.portfolio.total_trades,
            "winning_trades": self.portfolio.winning_trades,
            "losing_trades": self.portfolio.losing_trades,
            "entry_prices": self.entry_prices,
            "last_update": datetime.now().isoformat()
        }
        with open("data/paper_trading/portfolio.json", "w") as f:
            json.dump(data, f, indent=2)
    
    def log_trade(self, trade: Trade):
        """Registra trade en CSV"""
        filename = "data/paper_trading/trades.csv"
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'pair', 'action', 'price', 'amount_usd', 'quantity', 'reason'])
            writer.writerow([
                trade.timestamp, trade.pair, trade.action,
                trade.price, trade.amount_usd, trade.quantity, trade.reason
            ])
    
    def get_all_tickers(self) -> Dict[str, dict]:
        """Obtiene todos los precios"""
        try:
            response = requests.get(f"{self.BASE_URL}/ticker/24hr", timeout=15)
            return {item['symbol']: item for item in response.json()}
        except:
            return {}
    
    def get_top_altcoins(self, min_volume: float = 300000, limit: int = 200) -> List[tuple]:
        """Obtiene altcoins por volumen"""
        tickers = self.get_all_tickers()
        pairs = []
        
        for symbol, data in tickers.items():
            if symbol.endswith('USDT') and not symbol.startswith('USD'):
                try:
                    quote_volume = float(data['quoteVolume'])
                    if quote_volume >= min_volume:
                        # Excluir stablecoins y majors
                        if symbol not in ['BTCUSDT', 'ETHUSDT', 'USDCUSDT', 'BUSDUSDT', 'DAIUSDT', 'FDUSDUSDT']:
                            pairs.append((symbol, quote_volume, data))
                except:
                    continue
        
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:limit]
    
    def calculate_portfolio_value(self, tickers: Dict) -> float:
        """Calcula valor total del portfolio"""
        total = self.portfolio.cash
        for pair, quantity in self.portfolio.positions.items():
            if pair in tickers:
                price = float(tickers[pair]['lastPrice'])
                total += quantity * price
        return total
    
    def should_buy(self, pair: str, current_price: float, change_pct: float, 
                   volume: float, data: dict) -> tuple:
        """Estrategia de compra"""
        # No comprar si ya tenemos posición
        if pair in self.portfolio.positions and self.portfolio.positions[pair] > 0:
            return False, ""
        
        # No comprar si no hay cash suficiente
        if self.portfolio.cash < 10:  # Mínimo $10 por trade
            return False, ""
        
        # Estrategia: Comprar en caída fuerte (>5% en 2 min)
        if change_pct < -5 and volume > 500000:
            # Invertir máximo 20% del cash disponible por trade
            max_investment = min(self.portfolio.cash * 0.20, 25)  # Máx $25 por trade
            if max_investment >= 10:
                return True, f"CAIDA_FUERTE_{change_pct:.1f}%"
        
        # Estrategia: Comprar en rebote después de caída (-3% a -5%)
        if -5 < change_pct < -3 and volume > 1000000:
            max_investment = min(self.portfolio.cash * 0.15, 20)
            if max_investment >= 10:
                return True, f"REBOTE_POTENCIAL_{change_pct:.1f}%"
        
        return False, ""
    
    def should_sell(self, pair: str, current_price: float, change_pct: float) -> tuple:
        """Estrategia de venta"""
        if pair not in self.portfolio.positions or self.portfolio.positions[pair] <= 0:
            return False, ""
        
        entry_price = self.entry_prices.get(pair, current_price)
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Take profit: +8% o más
        if profit_pct >= 8:
            return True, f"TAKE_PROFIT_{profit_pct:.1f}%"
        
        # Stop loss: -5%
        if profit_pct <= -5:
            return True, f"STOP_LOSS_{profit_pct:.1f}%"
        
        # Subida fuerte en corto tiempo (+5% en 2 min) - tomar ganancias parciales
        if change_pct > 5 and profit_pct > 3:
            return True, f"GANANCIA_RAPIDA_{profit_pct:.1f}%"
        
        return False, ""
    
    def execute_buy(self, pair: str, price: float, amount_usd: float, reason: str):
        """Ejecuta compra simulada"""
        quantity = amount_usd / price
        
        self.portfolio.cash -= amount_usd
        self.portfolio.positions[pair] = self.portfolio.positions.get(pair, 0) + quantity
        self.entry_prices[pair] = price
        
        trade = Trade(
            timestamp=datetime.now().isoformat(),
            pair=pair,
            action="BUY",
            price=price,
            amount_usd=amount_usd,
            quantity=quantity,
            reason=reason
        )
        self.portfolio.trade_history.append(trade)
        self.portfolio.total_trades += 1
        self.log_trade(trade)
        
        print(f"\n🟢 COMPRA: {pair}")
        print(f"   Cantidad: {quantity:.6f}")
        print(f"   Precio: ${price:.6f}")
        print(f"   Invertido: ${amount_usd:.2f}")
        print(f"   Razón: {reason}")
        print(f"   Cash restante: ${self.portfolio.cash:.2f}")
    
    def execute_sell(self, pair: str, price: float, reason: str, partial: bool = False):
        """Ejecuta venta simulada"""
        if pair not in self.portfolio.positions:
            return
        
        quantity = self.portfolio.positions[pair]
        if partial:
            quantity = quantity * 0.5  # Vender 50%
        
        amount_usd = quantity * price
        entry_price = self.entry_prices.get(pair, price)
        profit_pct = ((price - entry_price) / entry_price) * 100
        
        self.portfolio.cash += amount_usd
        
        if partial:
            self.portfolio.positions[pair] -= quantity
        else:
            self.portfolio.positions[pair] = 0
            del self.entry_prices[pair]
        
        trade = Trade(
            timestamp=datetime.now().isoformat(),
            pair=pair,
            action="SELL",
            price=price,
            amount_usd=amount_usd,
            quantity=quantity,
            reason=reason
        )
        self.portfolio.trade_history.append(trade)
        self.portfolio.total_trades += 1
        
        if profit_pct > 0:
            self.portfolio.winning_trades += 1
        else:
            self.portfolio.losing_trades += 1
        
        self.log_trade(trade)
        
        emoji = "🟢" if profit_pct > 0 else "🔴"
        print(f"\n{emoji} VENTA: {pair}")
        print(f"   Cantidad: {quantity:.6f}")
        print(f"   Precio: ${price:.6f}")
        print(f"   Recibido: ${amount_usd:.2f}")
        print(f"   Ganancia/Pérdida: {profit_pct:+.2f}%")
        print(f"   Razón: {reason}")
        print(f"   Cash disponible: ${self.portfolio.cash:.2f}")
    
    def run_cycle(self):
        """Ejecuta un ciclo de trading"""
        print(f"\n{'='*80}")
        print(f"🤖 PAPER TRADING BOT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # Obtener datos
        tickers = self.get_all_tickers()
        if not tickers:
            print("❌ Error obteniendo datos")
            return
        
        # Actualizar valor del portfolio
        portfolio_value = self.calculate_portfolio_value(tickers)
        pnl_pct = ((portfolio_value - self.initial_cash) / self.initial_cash) * 100
        
        print(f"\n💰 Portfolio: ${portfolio_value:.2f} ({pnl_pct:+.2f}%)")
        print(f"   Cash: ${self.portfolio.cash:.2f}")
        print(f"   Posiciones abiertas: {len([p for p in self.portfolio.positions.values() if p > 0])}")
        print(f"   Trades: {self.portfolio.total_trades} (✓{self.portfolio.winning_trades} ✗{self.portfolio.losing_trades})")
        
        # Guardar historial de valor
        with open("data/paper_trading/portfolio_history.csv", 'a', newline='') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(['timestamp', 'portfolio_value', 'cash', 'pnl_pct'])
            writer.writerow([datetime.now().isoformat(), portfolio_value, self.portfolio.cash, pnl_pct])
        
        # Obtener altcoins para monitorear
        altcoins = self.get_top_altcoins(min_volume=300000, limit=150)
        print(f"\n📊 Analizando {len(altcoins)} altcoins...")
        
        trades_executed = 0
        
        # Primero verificar posiciones abiertas (ventas)
        for pair in list(self.portfolio.positions.keys()):
            if self.portfolio.positions[pair] > 0 and pair in tickers:
                data = tickers[pair]
                current_price = float(data['lastPrice'])
                
                # Calcular cambio desde último precio
                if pair in self.price_history:
                    prev_price = self.price_history[pair][-1] if self.price_history[pair] else current_price
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                else:
                    change_pct = 0
                
                should_sell_flag, reason = self.should_sell(pair, current_price, change_pct)
                if should_sell_flag:
                    self.execute_sell(pair, current_price, reason)
                    trades_executed += 1
        
        # Luego buscar compras (solo si tenemos cash)
        if self.portfolio.cash >= 10 and trades_executed < 3:  # Máx 3 trades por ciclo
            for symbol, volume, data in altcoins:
                if trades_executed >= 3:
                    break
                
                if symbol not in tickers:
                    continue
                
                current_price = float(data['lastPrice'])
                
                # Calcular cambio
                if symbol in self.price_history and self.price_history[symbol]:
                    prev_price = self.price_history[symbol][-1]
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                else:
                    change_pct = float(data.get('priceChangePercent', 0))
                
                # Guardar historial
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                self.price_history[symbol].append(current_price)
                if len(self.price_history[symbol]) > 5:
                    self.price_history[symbol].pop(0)
                
                # Evaluar compra
                should_buy_flag, reason = self.should_buy(symbol, current_price, change_pct, volume, data)
                if should_buy_flag:
                    max_amount = min(self.portfolio.cash * 0.20, 25, self.portfolio.cash - 5)
                    if max_amount >= 10:
                        self.execute_buy(symbol, current_price, max_amount, reason)
                        trades_executed += 1
        
        if trades_executed == 0:
            print("   ⏳ Sin operaciones en este ciclo")
        
        self.save_portfolio()
        
        print(f"\n{'='*80}")
        print(f"✅ Ciclo completado - Próximo chequeo en 2 minutos")
        print(f"{'='*80}")
    
    def run_continuous(self):
        """Corre continuamente cada 2 minutos"""
        print("\n" + "="*80)
        print("🚀 PAPER TRADING BOT INICIADO")
        print("💵 Capital inicial: $100.00")
        print("⏱️  Intervalo: 2 minutos")
        print("🎯 Estrategia: Scalping altcoins")
        print("="*80 + "\n")
        
        # Calcular fecha de finalización (domingo 1 de febrero)
        end_date = datetime(2026, 2, 1, 23, 59, 0)
        
        while datetime.now() < end_date:
            try:
                self.run_cycle()
            except Exception as e:
                print(f"❌ Error en ciclo: {e}")
            
            # Esperar 2 minutos
            time.sleep(120)
        
        # Reporte final
        self.generate_final_report()
    
    def generate_final_report(self):
        """Genera reporte final"""
        tickers = self.get_all_tickers()
        final_value = self.calculate_portfolio_value(tickers)
        pnl = final_value - self.initial_cash
        pnl_pct = (pnl / self.initial_cash) * 100
        
        print("\n" + "="*80)
        print("📊 REPORTE FINAL - PAPER TRADING")
        print("="*80)
        print(f"\n💰 Capital inicial: ${self.initial_cash:.2f}")
        print(f"💰 Capital final: ${final_value:.2f}")
        print(f"📈 P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
        print(f"\n📊 Estadísticas:")
        print(f"   Total trades: {self.portfolio.total_trades}")
        print(f"   Ganadores: {self.portfolio.winning_trades}")
        print(f"   Perdedores: {self.portfolio.losing_trades}")
        if self.portfolio.total_trades > 0:
            win_rate = (self.portfolio.winning_trades / self.portfolio.total_trades) * 100
            print(f"   Win rate: {win_rate:.1f}%")
        print(f"\n💵 Cash disponible: ${self.portfolio.cash:.2f}")
        print(f"📦 Posiciones abiertas:")
        for pair, qty in self.portfolio.positions.items():
            if qty > 0 and pair in tickers:
                price = float(tickers[pair]['lastPrice'])
                value = qty * price
                print(f"   - {pair}: {qty:.6f} (${value:.2f})")
        print("="*80)
        
        # Guardar reporte
        report_file = "data/paper_trading/FINAL_REPORT.txt"
        with open(report_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("📊 REPORTE FINAL - PAPER TRADING (2 DÍAS)\n")
            f.write("="*80 + "\n\n")
            f.write(f"Capital inicial: ${self.initial_cash:.2f}\n")
            f.write(f"Capital final: ${final_value:.2f}\n")
            f.write(f"P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)\n\n")
            f.write(f"Total trades: {self.portfolio.total_trades}\n")
            f.write(f"Ganadores: {self.portfolio.winning_trades}\n")
            f.write(f"Perdedores: {self.portfolio.losing_trades}\n")
            if self.portfolio.total_trades > 0:
                win_rate = (self.portfolio.winning_trades / self.portfolio.total_trades) * 100
                f.write(f"Win rate: {win_rate:.1f}%\n")
        
        print(f"\n📄 Reporte guardado en: {report_file}")

if __name__ == "__main__":
    bot = PaperTradingBot(initial_cash=100.0)
    bot.run_continuous()
