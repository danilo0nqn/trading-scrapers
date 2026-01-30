"""
Configuración para SureBet Scraper
"""

# Casas de apuestas soportadas con sus URLs
BOOKMAKERS = {
    "betwarrior": {
        "name": "BetWarrior",
        "url": "https://betwarrior.bet.ar",
        "country": "AR",
        "enabled": True,
        "timeout": 30000,
    },
    "codere": {
        "name": "Codere",
        "url": "https://www.codere.com.ar",
        "country": "AR",
        "enabled": True,
        "timeout": 30000,
    },
    "bplay": {
        "name": "Bplay",
        "url": "https://bplay.bet.ar",
        "country": "AR",
        "enabled": True,
        "timeout": 30000,
    },
    "betsson": {
        "name": "Betsson",
        "url": "https://www.betsson.com",
        "country": "AR",
        "enabled": True,
        "timeout": 30000,
    },
}

# Ligas a monitorear
LIGAS = {
    # Argentina
    "Primera Division": {
        "country": "Argentina",
        "competition_id": "argentina_primera_division",
        "priority": 1,
    },
    "Copa Argentina": {
        "country": "Argentina",
        "competition_id": "argentina_copa",
        "priority": 2,
    },
    "Primera Nacional": {
        "country": "Argentina",
        "competition_id": "argentina_primera_nacional",
        "priority": 3,
    },
    
    # Europa - Principales ligas
    "Premier League": {
        "country": "Inglaterra",
        "competition_id": "england_premier_league",
        "priority": 1,
    },
    "La Liga": {
        "country": "España",
        "competition_id": "spain_la_liga",
        "priority": 1,
    },
    "Serie A": {
        "country": "Italia",
        "competition_id": "italy_serie_a",
        "priority": 1,
    },
    "Bundesliga": {
        "country": "Alemania",
        "competition_id": "germany_bundesliga",
        "priority": 1,
    },
    "Ligue 1": {
        "country": "Francia",
        "competition_id": "france_ligue_1",
        "priority": 1,
    },
    
    # Champions y Europa League
    "Champions League": {
        "country": "Europa",
        "competition_id": "uefa_champions_league",
        "priority": 1,
    },
    "Europa League": {
        "country": "Europa",
        "competition_id": "uefa_europa_league",
        "priority": 2,
    },
}

# Configuración de surebets
SUREBET_CONFIG = {
    "margen_minimo": 1.0,  # Porcentaje mínimo de margen para considerar surebet
    "margen_maximo": 10.0,  # Porcentaje máximo (evitar errores/obvios)
    "stake_default": 10000,  # Stake total por defecto (en ARS)
    "max_stake_per_bookmaker": 50000,  # Máximo por casa
    "min_odds": 1.1,  # Odds mínimas a considerar
    "max_odds": 50.0,  # Odds máximas a considerar
}

# Selectores CSS/XPath para cada bookmaker (pueden variar, requieren mantenimiento)
SELECTORS = {
    "betwarrior": {
        "event_container": "[data-testid='event-item'], .event-item, .match-row",
        "team_names": ".team-name, .participant-name, [data-testid='team-name']",
        "odds": ".odd-value, .price, [data-testid='odd-value']",
        "event_time": ".event-time, .match-time, [data-testid='event-time']",
        "accept_cookies": "button[data-testid='accept-cookies'], .accept-cookies, #onetrust-accept-btn-handler",
    },
    "codere": {
        "event_container": ".event, .sports-event, [data-testid='sports-event']",
        "team_names": ".team, .participant, .event-name",
        "odds": ".odd, .price, .selection-price",
        "event_time": ".time, .event-time",
        "accept_cookies": ".cookie-accept, #acceptCookies, button[aria-label='Aceptar cookies']",
    },
    "bplay": {
        "event_container": ".event-card, .match-item, [data-testid='event-card']",
        "team_names": ".team, .participant-name",
        "odds": ".odd, .price-value",
        "event_time": ".match-time, .event-date",
        "accept_cookies": ".accept-cookies, button[data-testid='accept-cookies']",
    },
    "betsson": {
        "event_container": ".event, .match, [data-testid='event']",
        "team_names": ".team-name, .participant",
        "odds": ".odds, .price, .selection-odds",
        "event_time": ".time, .match-time",
        "accept_cookies": "#accept-cookies, .cookie-consent-accept",
    },
}

# User agents para evitar detección
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Delay entre requests (ms)
DELAYS = {
    "entre_paginas": 2000,
    "entre_casas": 3000,
    "despues_cookies": 1000,
}

# Directorio de salida
OUTPUT_DIR = "data"
