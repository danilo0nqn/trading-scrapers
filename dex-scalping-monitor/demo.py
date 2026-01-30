#!/usr/bin/env python3
"""
DEX Scalping Monitor - DEMO (Sin dependencias externas)
=======================================================
Ejemplo de ejecución mostrando cómo funciona el monitor.
"""

import random
from datetime import datetime

# Simulación de colores ANSI
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BG_GREEN = '\033[42m'
    BG_BLACK = '\033[40m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    print(f"\n{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}  DEX Scalping Monitor v1.0 - DEMO MODE{Colors.RESET}")
    print(f"{Colors.CYAN}  Monitoreando Uniswap V3 & PancakeSwap{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")

def print_connection_status():
    print(f"{Colors.GREEN}✓ Ethereum conectado (Chain ID: 1){Colors.RESET}")
    print(f"{Colors.GREEN}✓ BSC conectado (Chain ID: 56){Colors.RESET}")
    print(f"{Colors.GREEN}✓ Cargados 3 pares para monitoreo{Colors.RESET}\n")

def print_config():
    print(f"{Colors.YELLOW}Configuración:{Colors.RESET}")
    print(f"  • Umbral de cambio de precio: 5.0%")
    print(f"  • ROI mínimo viable: 10.0%")
    print(f"  • Intervalo de monitoreo: 60s")
    print(f"  • Monto de trade: $1,000 USD\n")

def print_scanning():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{Colors.CYAN}[{timestamp}] Escaneando oportunidades...{Colors.RESET}")

def print_table(opportunities):
    print(f"\n{Colors.BOLD}{'PAR':<20} {'CAMBIO(1m)':<12} {'VOLUMEN 24h':<15} {'GAS FEE':<10} {'ROI':<10} {'ESTADO':<12}{Colors.RESET}")
    print("-" * 85)
    
    for opp in opportunities:
        change_color = Colors.RED if opp['change'] > 0 else Colors.GREEN if opp['change'] < 0 else Colors.RESET
        status = f"{Colors.BG_GREEN}{Colors.BG_BLACK} ✓ VIABLE {Colors.RESET}" if opp['viable'] else ""
        
        print(f"{opp['pair']:<20} {change_color}{opp['change']:>+6.2f}%{Colors.RESET:<5} ${opp['volume']:>10,.0f}{Colors.RESET}   ${opp['gas']:>6.2f}    {Colors.YELLOW}{opp['roi']:>+5.1f}%{Colors.RESET}   {status}")

def print_alert(opportunity):
    print(f"\n{Colors.BG_GREEN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BG_GREEN} 🚨 ¡OPORTUNIDAD DE SCALPING DETECTADA!{Colors.RESET}")
    print(f"{Colors.BG_GREEN}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}Par:{Colors.RESET} {opportunity['pair']}")
    print(f"{Colors.CYAN}DEX:{Colors.RESET} {opportunity['dex']}")
    print(f"{Colors.CYAN}Cambio de Precio:{Colors.RESET} {Colors.RED}+{opportunity['change']:.2f}%{Colors.RESET}")
    print(f"{Colors.CYAN}Precio anterior:{Colors.RESET} ${opportunity['price_old']:.8f}")
    print(f"{Colors.CYAN}Precio actual:{Colors.RESET} ${opportunity['price_new']:.8f}")
    print(f"{Colors.CYAN}Volumen 24h:{Colors.RESET} ${opportunity['volume']:,.2f}")
    print(f"{Colors.CYAN}Liquidez:{Colors.RESET} {opportunity['liquidity']:,.0f}")
    print(f"{Colors.CYAN}Gas Fee:{Colors.RESET} ${opportunity['gas']:.2f}")
    print(f"{Colors.CYAN}Ganancia Potencial:{Colors.RESET} ${opportunity['profit']:.2f}")
    print(f"{Colors.YELLOW}{Colors.BOLD}ROI después de fees: {opportunity['roi']:.2f}%{Colors.RESET}")
    print(f"{Colors.BG_GREEN}{'='*80}{Colors.RESET}\n")
    
    print(f"{Colors.MAGENTA}💡 Recomendación:{Colors.RESET}")
    if opportunity['roi'] >= 10:
        print(f"  {Colors.GREEN}✓ Oportunidad VIABLE - Considerar entrada{Colors.RESET}")
    else:
        print(f"  {Colors.YELLOW}⚠ Margen ajustado - Evaluar riesgo{Colors.RESET}")
    
    print(f"\n{Colors.BLUE}📊 Análisis:{Colors.RESET}")
    print(f"  • Movimiento brusco detectado en 1 minuto")
    print(f"  • Volumen suficiente para operar")
    print(f"  • Gas fees dentro de rangos aceptables")

def generate_opportunities():
    """Genera oportunidades simuladas"""
    pairs = [
        {"pair": "WETH/USDC", "dex": "Uniswap V3", "volume": 125000000, "liquidity": 500000000},
        {"pair": "PEPE/WETH", "dex": "Uniswap V3", "volume": 5200000, "liquidity": 2500000},
        {"pair": "SHIB/WETH", "dex": "Uniswap V3", "volume": 8500000, "liquidity": 4200000},
        {"pair": "DOGE/WETH", "dex": "Uniswap V3", "volume": 3200000, "liquidity": 1800000},
        {"pair": "WBNB/BUSD", "dex": "PancakeSwap", "volume": 45000000, "liquidity": 120000000},
    ]
    
    opportunities = []
    for p in pairs:
        # Generar cambio de precio aleatorio
        change = random.uniform(-12, 12)
        
        # Calcular gas fee (simulado)
        gas = random.uniform(8, 25)
        
        # Calcular ROI potencial
        profit = abs(change) * 10  # $1000 * change% / 100
        roi = profit - gas
        
        viable = abs(change) >= 5 and roi >= 10
        
        opportunities.append({
            "pair": p["pair"],
            "dex": p["dex"],
            "change": change,
            "volume": p["volume"],
            "liquidity": p["liquidity"],
            "gas": gas,
            "profit": profit,
            "roi": roi,
            "viable": viable,
            "price_old": random.uniform(0.000001, 1.0),
            "price_new": random.uniform(0.000001, 1.0)
        })
    
    return opportunities

def main():
    print_header()
    print_connection_status()
    print_config()
    
    print("Presiona Ctrl+C para salir\n")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            print_scanning()
            
            # Generar oportunidades simuladas
            opportunities = generate_opportunities()
            
            # Mostrar tabla
            print_table(opportunities)
            
            # Verificar si hay oportunidades viables
            viable_opps = [o for o in opportunities if o['viable']]
            
            if viable_opps:
                for opp in viable_opps:
                    print_alert(opp)
                    print(f"\n{Colors.GREEN}✓ Oportunidad guardada en historico{Colors.RESET}")
            else:
                print(f"\n{Colors.YELLOW}No se detectaron oportunidades viables en este scan.{Colors.RESET}")
            
            print(f"\n{Colors.BLUE}[Scan #{iteration}] Próximo scan en 60 segundos...{Colors.RESET}")
            print("-" * 80)
            
            # En demo, solo hacemos 3 iteraciones
            if iteration >= 3:
                print(f"\n{Colors.GREEN}Demo completado!{Colors.RESET}")
                print(f"\n{Colors.CYAN}Para ejecutar con datos reales:{Colors.RESET}")
                print("  1. Copia .env.example a .env")
                print("  2. Añade tu API key de Alchemy/Infura")
                print("  3. Ejecuta: python3 dex_monitor.py")
                break
            
            import time
            time.sleep(3)  # Espera corta para demo
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Monitor detenido por el usuario.{Colors.RESET}")
        print(f"{Colors.GREEN}Historico guardado. ¡Hasta luego!{Colors.RESET}")

if __name__ == "__main__":
    main()
