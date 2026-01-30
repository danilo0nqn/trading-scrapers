#!/usr/bin/env python3
"""
SureBet Scraper - Detector de Oportunidades de Arbitrage
Para casas de apuestas argentinas

Uso:
    python surebet_scraper.py [opciones]

Ejemplo:
    python surebet_scraper.py --ligas "Primera Division,Premier League" --margen 1.5
"""

import asyncio
import json
import csv
import os
import re
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import random

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Browser = BrowserContext = Any

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except ImportError:
    class _Fore:
        def __getattr__(self, name):
            return ""
    class _Style:
        def __getattr__(self, name):
            return ""
    Fore = _Fore()
    Style = _Style()
    colorama_init = lambda **kwargs: None

from config import (
    BOOKMAKERS, LIGAS, SUREBET_CONFIG, SELECTORS, 
    USER_AGENTS, DELAYS, OUTPUT_DIR
)


@dataclass
class Odd:
    """Representa una odd para un resultado específico"""
    bookmaker: str
    outcome: str  # '1', 'X', '2', 'Over', 'Under', etc.
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "bookmaker": self.bookmaker,
            "outcome": self.outcome,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Match:
    """Representa un partido con sus odds"""
    home_team: str
    away_team: str
    league: str
    country: str
    match_time: Optional[str] = None
    odds: Dict[str, List[Odd]] = field(default_factory=dict)  # market -> odds
    
    @property
    def name(self) -> str:
        return f"{self.home_team} vs {self.away_team}"
    
    def to_dict(self) -> Dict:
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "league": self.league,
            "country": self.country,
            "match_time": self.match_time,
            "odds": {k: [o.to_dict() for o in v] for k, v in self.odds.items()},
        }


@dataclass
class SureBet:
    """Representa una oportunidad de surebet"""
    match: Match
    market: str
    margin: float  # Porcentaje de margen
    roi: float  # Retorno de inversión
    stakes: List[Dict]  # Distribución de stakes
    total_stake: float
    guaranteed_profit: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "match": self.match.to_dict(),
            "market": self.market,
            "margin": self.margin,
            "roi": self.roi,
            "stakes": self.stakes,
            "total_stake": self.total_stake,
            "guaranteed_profit": self.guaranteed_profit,
            "timestamp": self.timestamp.isoformat(),
        }


class BookmakerScraper:
    """Scraper base para casas de apuestas"""
    
    def __init__(self, bookmaker_id: str, headless: bool = True):
        self.bookmaker_id = bookmaker_id
        self.config = BOOKMAKERS[bookmaker_id]
        self.selectors = SELECTORS[bookmaker_id]
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    async def init_browser(self, playwright):
        """Inicializa el navegador"""
        self.browser = await playwright.chromium.launch(headless=self.headless)
        
        # Crear contexto con user agent aleatorio
        user_agent = random.choice(USER_AGENTS)
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="es-AR",
            timezone_id="America/Buenos_Aires",
        )
        
        self.page = await self.context.new_page()
        
        # Interceptar y bloquear recursos innecesarios
        await self.page.route("**/*", lambda route, request: 
            route.abort() if request.resource_type in ["image", "media", "font"] 
            else route.continue_()
        )
    
    async def close(self):
        """Cierra el navegador"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def accept_cookies(self):
        """Acepta cookies si aparece el banner"""
        try:
            selectors = self.selectors["accept_cookies"].split(", ")
            for selector in selectors:
                try:
                    await self.page.click(selector, timeout=3000)
                    print(f"  {Fore.GREEN}✓ Cookies aceptadas")
                    await asyncio.sleep(DELAYS["despues_cookies"] / 1000)
                    return
                except:
                    continue
        except:
            pass
    
    async def scrape_football_odds(self, league_filter: Optional[List[str]] = None) -> List[Match]:
        """
        Scrapea odds de fútbol.
        
        Nota: Esta es una implementación de ejemplo/simulación.
        Las casas de apuestas reales requieren mantenimiento continuo de selectores
        y pueden tener protecciones anti-scraping.
        """
        matches = []
        
        try:
            print(f"\n{Fore.CYAN}Scrapeando {self.config['name']}...")
            
            # Navegar a la página de fútbol
            await self.page.goto(f"{self.config['url']}/sports/futbol", 
                                 timeout=self.config["timeout"])
            
            await self.page.wait_for_load_state("networkidle")
            await self.accept_cookies()
            
            # Esperar a que carguen los eventos
            await asyncio.sleep(2)
            
            # En una implementación real, aquí se extraerían los datos del DOM
            # Por ahora, simulamos datos para demostración
            matches = await self._extract_matches(league_filter)
            
            print(f"  {Fore.GREEN}✓ Encontrados {len(matches)} partidos")
            
        except Exception as e:
            print(f"  {Fore.RED}✗ Error: {e}")
        
        return matches
    
    async def _extract_matches(self, league_filter: Optional[List[str]] = None) -> List[Match]:
        """
        Extrae partidos de la página.
        
        Nota: Implementación simulada con datos de ejemplo.
        Para producción, implementar extracción real del DOM.
        """
        matches = []
        
        # Datos de ejemplo para demostración
        sample_matches = self._get_sample_data()
        
        if league_filter:
            sample_matches = [m for m in sample_matches if m.league in league_filter]
        
        return sample_matches
    
    def _get_sample_data(self) -> List[Match]:
        """Genera datos de ejemplo para demostración"""
        # Datos de ejemplo - en producción vendrían del scraping real
        sample_data = [
            {
                "home": "Boca Juniors",
                "away": "River Plate",
                "league": "Primera Division",
                "country": "Argentina",
                "odds": {
                    "1X2": [
                        {"bookmaker": self.config["name"], "outcome": "1", "value": 2.45},
                        {"bookmaker": self.config["name"], "outcome": "X", "value": 3.20},
                        {"bookmaker": self.config["name"], "outcome": "2", "value": 3.10},
                    ]
                }
            },
            {
                "home": "Racing Club",
                "away": "Independiente",
                "league": "Primera Division",
                "country": "Argentina",
                "odds": {
                    "1X2": [
                        {"bookmaker": self.config["name"], "outcome": "1", "value": 2.10},
                        {"bookmaker": self.config["name"], "outcome": "X", "value": 3.40},
                        {"bookmaker": self.config["name"], "outcome": "2", "value": 3.80},
                    ]
                }
            },
            {
                "home": "San Lorenzo",
                "away": "Huracán",
                "league": "Primera Division",
                "country": "Argentina",
                "odds": {
                    "1X2": [
                        {"bookmaker": self.config["name"], "outcome": "1", "value": 2.30},
                        {"bookmaker": self.config["name"], "outcome": "X", "value": 3.10},
                        {"bookmaker": self.config["name"], "outcome": "2", "value": 3.50},
                    ]
                }
            },
        ]
        
        matches = []
        for data in sample_data:
            match = Match(
                home_team=data["home"],
                away_team=data["away"],
                league=data["league"],
                country=data["country"],
            )
            
            for market, odds_list in data["odds"].items():
                match.odds[market] = [
                    Odd(
                        bookmaker=o["bookmaker"],
                        outcome=o["outcome"],
                        value=o["value"]
                    )
                    for o in odds_list
                ]
            
            matches.append(match)
        
        return matches


class SureBetDetector:
    """Detecta oportunidades de surebet"""
    
    def __init__(self, config: Dict = SUREBET_CONFIG):
        self.config = config
    
    def find_surebets(self, matches: List[Match], total_stake: float) -> List[SureBet]:
        """Busca oportunidades de surebet en una lista de partidos"""
        surebets = []
        
        for match in matches:
            for market, odds_list in match.odds.items():
                surebet = self._analyze_market(match, market, odds_list, total_stake)
                if surebet:
                    surebets.append(surebet)
        
        return surebets
    
    def _analyze_market(self, match: Match, market: str, 
                        odds_list: List[Odd], total_stake: float) -> Optional[SureBet]:
        """Analiza un mercado específico en busca de surebets"""
        
        # Agrupar odds por resultado
        outcomes = {}
        for odd in odds_list:
            if odd.outcome not in outcomes:
                outcomes[odd.outcome] = []
            outcomes[odd.outcome].append(odd)
        
        # Para cada resultado, tomar la mejor odd
        best_odds = {}
        for outcome, odds in outcomes.items():
            best = max(odds, key=lambda x: x.value)
            best_odds[outcome] = best
        
        # Calcular margen de arbitrage
        margin = self._calculate_margin(best_odds)
        
        if margin < self.config["margen_minimo"]:
            return None
        
        if margin > self.config["margen_maximo"]:
            # Margen sospechosamente alto, posible error
            return None
        
        # Calcular stakes óptimos
        stakes = self._calculate_stakes(best_odds, total_stake)
        
        # Calcular ganancia garantizada
        guaranteed_profit = self._calculate_profit(stakes, best_odds)
        roi = (guaranteed_profit / total_stake) * 100
        
        return SureBet(
            match=match,
            market=market,
            margin=margin,
            roi=roi,
            stakes=stakes,
            total_stake=total_stake,
            guaranteed_profit=guaranteed_profit,
        )
    
    def _calculate_margin(self, best_odds: Dict[str, Odd]) -> float:
        """Calcula el margen de arbitrage"""
        # Fórmula: 1/sum(1/odds) - 1
        sum_inverse = sum(1 / odd.value for odd in best_odds.values())
        
        if sum_inverse >= 1:
            return 0  # No hay arbitrage
        
        margin = (1 - sum_inverse) * 100
        return margin
    
    def _calculate_stakes(self, best_odds: Dict[str, Odd], 
                          total_stake: float) -> List[Dict]:
        """Calcula la distribución óptima de stakes (proporcional)"""
        
        # Calcular pesos inversos
        weights = {outcome: 1 / odd.value for outcome, odd in best_odds.items()}
        total_weight = sum(weights.values())
        
        stakes = []
        for outcome, odd in best_odds.items():
            weight = weights[outcome]
            stake = (weight / total_weight) * total_stake
            expected_return = stake * odd.value
            
            stakes.append({
                "outcome": outcome,
                "bookmaker": odd.bookmaker,
                "odds": odd.value,
                "stake": round(stake, 2),
                "expected_return": round(expected_return, 2),
            })
        
        return stakes
    
    def _calculate_profit(self, stakes: List[Dict], best_odds: Dict[str, Odd]) -> float:
        """Calcula la ganancia garantizada"""
        # Todas las apuestas deben retornar lo mismo
        return stakes[0]["expected_return"] - sum(s["stake"] for s in stakes)


class DataExporter:
    """Exporta datos a diferentes formatos"""
    
    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def export_odds(self, all_matches: Dict[str, List[Match]]):
        """Exporta todas las odds a CSV"""
        rows = []
        
        for bookmaker, matches in all_matches.items():
            for match in matches:
                for market, odds_list in match.odds.items():
                    for odd in odds_list:
                        rows.append({
                            "bookmaker": bookmaker,
                            "league": match.league,
                            "country": match.country,
                            "home_team": match.home_team,
                            "away_team": match.away_team,
                            "match_time": match.match_time,
                            "market": market,
                            "outcome": odd.outcome,
                            "odds": odd.value,
                            "timestamp": odd.timestamp.isoformat(),
                        })
        
        filepath = self.output_dir / f"odds_{self.timestamp}.csv"
        
        if PANDAS_AVAILABLE and rows:
            df = pd.DataFrame(rows)
            df.to_csv(filepath, index=False)
        elif rows:
            # Fallback sin pandas
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        else:
            # Crear archivo vacío con headers
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                f.write("bookmaker,league,country,home_team,away_team,match_time,market,outcome,odds,timestamp\n")
        
        print(f"\n{Fore.GREEN}✓ Odds exportadas a: {filepath}")
        return filepath
    
    def export_surebets(self, surebets: List[SureBet], format: str = "both"):
        """Exporta surebets a JSON y/o CSV"""
        filepaths = []
        
        if format in ("json", "both"):
            filepath = self._export_surebets_json(surebets)
            filepaths.append(filepath)
        
        if format in ("csv", "both"):
            filepath = self._export_surebets_csv(surebets)
            filepaths.append(filepath)
        
        return filepaths
    
    def _export_surebets_json(self, surebets: List[SureBet]) -> Path:
        """Exporta surebets a JSON"""
        data = {
            "generated_at": datetime.now().isoformat(),
            "count": len(surebets),
            "surebets": [sb.to_dict() for sb in surebets],
        }
        
        filepath = self.output_dir / f"surebets_{self.timestamp}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.GREEN}✓ Surebets exportados a JSON: {filepath}")
        return filepath
    
    def _export_surebets_csv(self, surebets: List[SureBet]) -> Path:
        """Exporta surebets a CSV"""
        rows = []
        
        for sb in surebets:
            base_info = {
                "match": sb.match.name,
                "league": sb.match.league,
                "market": sb.market,
                "margin_percent": round(sb.margin, 2),
                "roi_percent": round(sb.roi, 2),
                "total_stake": sb.total_stake,
                "guaranteed_profit": round(sb.guaranteed_profit, 2),
                "detected_at": sb.timestamp.isoformat(),
            }
            
            for stake in sb.stakes:
                row = {
                    **base_info,
                    "outcome": stake["outcome"],
                    "bookmaker": stake["bookmaker"],
                    "odds": stake["odds"],
                    "stake": stake["stake"],
                    "expected_return": stake["expected_return"],
                }
                rows.append(row)
        
        filepath = self.output_dir / f"surebets_{self.timestamp}.csv"
        
        if PANDAS_AVAILABLE and rows:
            df = pd.DataFrame(rows)
            df.to_csv(filepath, index=False)
        elif rows:
            # Fallback sin pandas
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        else:
            # Crear archivo vacío
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("No surebets found\n")
        
        print(f"{Fore.GREEN}✓ Surebets exportados a CSV: {filepath}")
        return filepath


def print_surebet(surebet: SureBet):
    """Imprime una oportunidad de surebet de forma legible"""
    print(f"\n{Fore.YELLOW}{'='*60}")
    print(f"{Fore.GREEN}🎯 OPORTUNIDAD SUREBET DETECTADA")
    print(f"{Fore.YELLOW}{'='*60}")
    
    print(f"\n{Fore.CYAN}📅 Partido: {surebet.match.name}")
    print(f"{Fore.CYAN}🏆 Liga: {surebet.match.league}")
    print(f"{Fore.CYAN}📊 Mercado: {surebet.market}")
    
    print(f"\n{Fore.WHITE}💰 Distribución óptima (Stake total: ${surebet.total_stake:,.2f}):")
    print(f"{Fore.WHITE}{'-'*50}")
    
    for stake in surebet.stakes:
        outcome_map = {"1": "Local", "X": "Empate", "2": "Visitante"}
        outcome_name = outcome_map.get(stake["outcome"], stake["outcome"])
        
        print(f"  {Fore.MAGENTA}• {outcome_name} ({stake['bookmaker']}):")
        print(f"    {Fore.WHITE}  Odds: {stake['odds']} | Stake: ${stake['stake']:,.2f} | Retorno: ${stake['expected_return']:,.2f}")
    
    print(f"\n{Fore.GREEN}📈 Resultado:")
    print(f"  • Margen: {surebet.margin:.2f}%")
    print(f"  • ROI: {surebet.roi:.2f}%")
    print(f"  • Ganancia garantizada: ${surebet.guaranteed_profit:,.2f}")
    print(f"{Fore.YELLOW}{'='*60}\n")


def simulate_surebet_example(total_stake: float = 10000) -> SureBet:
    """Genera un ejemplo de surebet para demostración"""
    
    match = Match(
        home_team="Boca Juniors",
        away_team="River Plate",
        league="Primera Division",
        country="Argentina",
        match_time="2024-01-20 20:00",
    )
    
    # Simular odds de diferentes casas que generan surebet REAL
    # Para surebet: 1/odds1 + 1/oddsX + 1/odds2 < 1
    # Ejemplo: 1/2.50 + 1/3.60 + 1/3.30 = 0.40 + 0.278 + 0.303 = 0.981 < 1 ✓
    match.odds["1X2"] = [
        Odd(bookmaker="BetWarrior", outcome="1", value=2.50),  # Mejor local
        Odd(bookmaker="BetWarrior", outcome="X", value=3.10),
        Odd(bookmaker="BetWarrior", outcome="2", value=3.00),
        Odd(bookmaker="Codere", outcome="1", value=2.35),
        Odd(bookmaker="Codere", outcome="X", value=3.60),  # Mejor empate
        Odd(bookmaker="Codere", outcome="2", value=3.15),
        Odd(bookmaker="Bplay", outcome="1", value=2.40),
        Odd(bookmaker="Bplay", outcome="X", value=3.20),
        Odd(bookmaker="Bplay", outcome="2", value=3.30),  # Mejor visitante
        Odd(bookmaker="Betsson", outcome="1", value=2.38),
        Odd(bookmaker="Betsson", outcome="X", value=3.25),
        Odd(bookmaker="Betsson", outcome="2", value=3.20),
    ]
    
    detector = SureBetDetector()
    surebets = detector.find_surebets([match], total_stake)
    
    return surebets[0] if surebets else None


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="SureBet Scraper - Detector de Arbitrage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python surebet_scraper.py
  python surebet_scraper.py --ligas "Primera Division,La Liga" --margen 1.5
  python surebet_scraper.py --stake 50000 --headless
        """
    )
    
    parser.add_argument(
        "--ligas",
        type=str,
        default=None,
        help="Ligas a escanear (separadas por coma)"
    )
    parser.add_argument(
        "--margen",
        type=float,
        default=SUREBET_CONFIG["margen_minimo"],
        help=f"Margen mínimo de surebet (default: {SUREBET_CONFIG['margen_minimo']})"
    )
    parser.add_argument(
        "--stake",
        type=float,
        default=SUREBET_CONFIG["stake_default"],
        help=f"Stake total disponible en ARS (default: {SUREBET_CONFIG['stake_default']})"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Ejecutar sin abrir navegador"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "csv", "both"],
        default="both",
        help="Formato de exportación (default: both)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        default=False,
        help="Modo demo con datos de ejemplo (sin scraping real)"
    )
    
    args = parser.parse_args()
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.WHITE}    🏆 SUREBET SCRAPER - DETECTOR DE ARBITRAGE 🏆")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    # Configurar parámetros
    league_filter = args.ligas.split(",") if args.ligas else None
    config = SUREBET_CONFIG.copy()
    config["margen_minimo"] = args.margen
    
    # Modo demo
    if args.demo:
        print(f"{Fore.YELLOW}🎮 MODO DEMO: Usando datos de ejemplo\n")
        
        # Generar ejemplo de surebet
        example_surebet = simulate_surebet_example(total_stake=args.stake)
        
        if example_surebet:
            print_surebet(example_surebet)
            
            # Exportar
            exporter = DataExporter()
            exporter.export_surebets([example_surebet], args.format)
        
        print(f"\n{Fore.GREEN}✓ Demo completado!")
        return
    
    # Modo scraping real
    if not PLAYWRIGHT_AVAILABLE:
        print(f"{Fore.RED}✗ Playwright no está instalado. Ejecutando en modo demo.")
        print(f"{Fore.YELLOW}   Instala con: pip install playwright && playwright install chromium\n")
        args.demo = True
    
    all_matches = {}
    all_surebets = []
    
    if PLAYWRIGHT_AVAILABLE and not args.demo:
        async with async_playwright() as playwright:
            for bookmaker_id, bm_config in BOOKMAKERS.items():
                if not bm_config["enabled"]:
                    continue
                
                async with BookmakerScraper(bookmaker_id, headless=args.headless) as scraper:
                    await scraper.init_browser(playwright)
                    
                    matches = await scraper.scrape_football_odds(league_filter)
                    all_matches[bm_config["name"]] = matches
                    
                    # Esperar entre casas
                    await asyncio.sleep(DELAYS["entre_casas"] / 1000)
    
    # Consolidar partidos por nombre
    consolidated_matches = {}
    for bookmaker, matches in all_matches.items():
        for match in matches:
            key = f"{match.home_team}|{match.away_team}"
            if key not in consolidated_matches:
                consolidated_matches[key] = match
            else:
                # Merge odds
                for market, odds in match.odds.items():
                    if market not in consolidated_matches[key].odds:
                        consolidated_matches[key].odds[market] = []
                    consolidated_matches[key].odds[market].extend(odds)
    
    match_list = list(consolidated_matches.values())
    print(f"\n{Fore.CYAN}Total partidos únicos: {len(match_list)}")
    
    # Detectar surebets
    print(f"\n{Fore.CYAN}🔍 Analizando oportunidades de arbitrage...")
    detector = SureBetDetector(config)
    all_surebets = detector.find_surebets(match_list, args.stake)
    
    # Mostrar resultados
    if all_surebets:
        print(f"\n{Fore.GREEN}🎉 Se encontraron {len(all_surebets)} oportunidades de surebet!")
        for sb in all_surebets:
            print_surebet(sb)
    else:
        print(f"\n{Fore.YELLOW}⚠ No se encontraron oportunidades de surebet con margen >= {args.margen}%")
    
    # Exportar datos
    exporter = DataExporter()
    exporter.export_odds(all_matches)
    if all_surebets:
        exporter.export_surebets(all_surebets, args.format)
    
    print(f"\n{Fore.GREEN}{'='*60}")
    print(f"{Fore.GREEN}    ✓ ANÁLISIS COMPLETADO")
    print(f"{Fore.GREEN}{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
