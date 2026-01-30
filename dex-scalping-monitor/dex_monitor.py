#!/usr/bin/env python3
"""
DEX Scalping Monitor
====================
Monitors Uniswap V3 (Ethereum) and PancakeSwap (BSC) for scalping opportunities.
Detects price movements >5% in 1 minute and calculates ROI potential.

Author: Clawdbot
Version: 1.0.0
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from decimal import Decimal

import requests
import pandas as pd
from web3 import Web3
from web3.middleware import geth_poa_middleware
from colorama import init, Fore, Back, Style
from tabulate import tabulate

from config import config

# Initialize colorama
init(autoreset=True)

# ============================================
# LOGGING SETUP
# ============================================
os.makedirs(os.path.dirname(config.LOG_FILE) if config.LOG_FILE else "logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class TokenPair:
    """Represents a token pair on a DEX"""
    address: str
    token0: str
    token0_symbol: str
    token1: str
    token1_symbol: str
    dex: str  # 'uniswap' or 'pancakeswap'
    chain: str  # 'ethereum' or 'bsc'
    fee_tier: int = 3000  # Default 0.3%
    
    def __str__(self):
        return f"{self.token0_symbol}/{self.token1_symbol} ({self.dex})"

@dataclass
class PriceData:
    """Price data for a token pair at a specific time"""
    pair: TokenPair
    price: float
    timestamp: datetime
    volume_24h: float = 0.0
    liquidity: float = 0.0
    
@dataclass
class Opportunity:
    """Represents a scalping opportunity"""
    pair: TokenPair
    price_change_pct: float
    price_old: float
    price_new: float
    volume_24h: float
    liquidity: float
    gas_fee_eth: float
    gas_fee_usd: float
    potential_profit_usd: float
    roi_after_fees: float
    timestamp: datetime
    is_viable: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'pair': str(self.pair),
            'dex': self.pair.dex,
            'token0': self.pair.token0_symbol,
            'token1': self.pair.token1_symbol,
            'price_change_pct': self.price_change_pct,
            'price_old': self.price_old,
            'price_new': self.price_new,
            'volume_24h': self.volume_24h,
            'liquidity': self.liquidity,
            'gas_fee_eth': self.gas_fee_eth,
            'gas_fee_usd': self.gas_fee_usd,
            'potential_profit_usd': self.potential_profit_usd,
            'roi_after_fees': self.roi_after_fees,
            'is_viable': self.is_viable
        }

# ============================================
# ABI DEFINITIONS
# ============================================

UNISWAP_V3_FACTORY_ABI = json.loads('''[
    {"inputs":[],"name":"feeAmountTickSpacing","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

UNISWAP_V3_POOL_ABI = json.loads('''[
    {"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"fee","outputs":[{"internalType":"uint24","name":"","type":"uint24"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"liquidity","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

# ============================================
# DEX MONITOR CLASS
# ============================================

class DEXMonitor:
    """Main class for monitoring DEX opportunities"""
    
    def __init__(self):
        self.price_history: Dict[str, List[PriceData]] = defaultdict(list)
        self.opportunity_history: List[Opportunity] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        
        # Initialize Web3 connections
        self.w3_eth = None
        self.w3_bsc = None
        
        # Initialize DEX contracts
        self.uniswap_factory = None
        self.pancakeswap_factory = None
        
        # ETH price for gas calculations
        self.eth_price_usd = 0.0
        self.bnb_price_usd = 0.0
        
        # Popular pairs to monitor
        self.monitored_pairs: List[TokenPair] = []
        
    def connect(self) -> bool:
        """Connect to Ethereum and BSC networks"""
        try:
            # Connect to Ethereum
            logger.info(f"{Fore.CYAN}Connecting to Ethereum...{Style.RESET_ALL}")
            self.w3_eth = Web3(Web3.HTTPProvider(config.ETHEREUM_RPC_URL))
            if self.w3_eth.is_connected():
                logger.info(f"{Fore.GREEN}✓ Ethereum connected (Chain ID: {self.w3_eth.eth.chain_id}){Style.RESET_ALL}")
            else:
                logger.error(f"{Fore.RED}✗ Failed to connect to Ethereum{Style.RESET_ALL}")
                self.w3_eth = None
                
        except Exception as e:
            logger.error(f"{Fore.RED}Ethereum connection error: {e}{Style.RESET_ALL}")
            self.w3_eth = None
            
        try:
            # Connect to BSC
            logger.info(f"{Fore.CYAN}Connecting to BSC...{Style.RESET_ALL}")
            self.w3_bsc = Web3(Web3.HTTPProvider(config.BSC_RPC_URL))
            # BSC uses PoA, add middleware
            self.w3_bsc.middleware_onion.inject(geth_poa_middleware, layer=0)
            if self.w3_bsc.is_connected():
                logger.info(f"{Fore.GREEN}✓ BSC connected (Chain ID: {self.w3_bsc.eth.chain_id}){Style.RESET_ALL}")
            else:
                logger.error(f"{Fore.RED}✗ Failed to connect to BSC{Style.RESET_ALL}")
                self.w3_bsc = None
                
        except Exception as e:
            logger.error(f"{Fore.RED}BSC connection error: {e}{Style.RESET_ALL}")
            self.w3_bsc = None
            
        # Initialize DEX contracts if connected
        if self.w3_eth:
            self.uniswap_factory = self.w3_eth.eth.contract(
                address=Web3.to_checksum_address(config.UNISWAP_V3_FACTORY),
                abi=UNISWAP_V3_FACTORY_ABI
            )
            
        if self.w3_bsc:
            self.pancakeswap_factory = self.w3_bsc.eth.contract(
                address=Web3.to_checksum_address(config.PANCAKESWAP_V3_FACTORY),
                abi=UNISWAP_V3_FACTORY_ABI  # Same ABI as Uniswap V3
            )
            
        return self.w3_eth is not None or self.w3_bsc is not None
    
    def fetch_eth_price(self) -> float:
        """Fetch current ETH price from CoinGecko"""
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,binancecoin&vs_currencies=usd",
                timeout=10
            )
            data = response.json()
            self.eth_price_usd = data.get('ethereum', {}).get('usd', 0)
            self.bnb_price_usd = data.get('binancecoin', {}).get('usd', 0)
            return self.eth_price_usd
        except Exception as e:
            logger.warning(f"Failed to fetch ETH price: {e}")
            return self.eth_price_usd or 3000.0
    
    def get_gas_price(self, chain: str) -> float:
        """Get current gas price in Gwei"""
        try:
            if chain == 'ethereum' and self.w3_eth:
                gas_price_wei = self.w3_eth.eth.gas_price
                return self.w3_eth.from_wei(gas_price_wei, 'gwei')
            elif chain == 'bsc' and self.w3_bsc:
                gas_price_wei = self.w3_bsc.eth.gas_price
                return self.w3_bsc.from_wei(gas_price_wei, 'gwei')
        except Exception as e:
            logger.warning(f"Failed to get gas price for {chain}: {e}")
        return 50.0  # Default fallback
    
    def calculate_gas_cost(self, chain: str) -> Tuple[float, float]:
        """Calculate gas cost in native token and USD"""
        gas_price_gwei = self.get_gas_price(chain)
        gas_limit = config.GAS_LIMIT_SWAP
        
        # Calculate gas cost in ETH/BNB
        gas_cost_native = (gas_price_gwei * gas_limit) / 1e9
        
        # Convert to USD
        if chain == 'ethereum':
            gas_cost_usd = gas_cost_native * self.eth_price_usd
        else:
            gas_cost_usd = gas_cost_native * self.bnb_price_usd
            
        return gas_cost_native, gas_cost_usd
    
    def load_popular_pairs(self) -> List[TokenPair]:
        """Load popular token pairs to monitor"""
        pairs = []
        
        # Ethereum Uniswap V3 pairs
        if self.w3_eth:
            popular_eth_pairs = [
                # WETH/USDC
                (config.WETH_ADDRESS, config.USDC_ADDRESS, 500),
                # WETH/USDT
                (config.WETH_ADDRESS, config.USDT_ADDRESS, 500),
                # USDC/USDT
                (config.USDC_ADDRESS, config.USDT_ADDRESS, 100),
            ]
            
            for token0, token1, fee in popular_eth_pairs:
                try:
                    pool_address = self.uniswap_factory.functions.getPool(
                        Web3.to_checksum_address(token0),
                        Web3.to_checksum_address(token1),
                        fee
                    ).call()
                    
                    if pool_address != '0x0000000000000000000000000000000000000000':
                        # Get token symbols
                        token0_contract = self.w3_eth.eth.contract(
                            address=Web3.to_checksum_address(token0), 
                            abi=ERC20_ABI
                        )
                        token1_contract = self.w3_eth.eth.contract(
                            address=Web3.to_checksum_address(token1), 
                            abi=ERC20_ABI
                        )
                        
                        symbol0 = token0_contract.functions.symbol().call()
                        symbol1 = token1_contract.functions.symbol().call()
                        
                        pair = TokenPair(
                            address=pool_address,
                            token0=token0,
                            token0_symbol=symbol0,
                            token1=token1,
                            token1_symbol=symbol1,
                            dex='uniswap',
                            chain='ethereum',
                            fee_tier=fee
                        )
                        pairs.append(pair)
                        logger.info(f"Added pair: {pair}")
                        
                except Exception as e:
                    logger.warning(f"Failed to load pair {token0}/{token1}: {e}")
        
        # BSC PancakeSwap pairs
        if self.w3_bsc:
            popular_bsc_pairs = [
                # WBNB/BUSD
                (config.WBNB_ADDRESS, config.BUSD_ADDRESS, 2500),
            ]
            
            for token0, token1, fee in popular_bsc_pairs:
                try:
                    pool_address = self.pancakeswap_factory.functions.getPool(
                        Web3.to_checksum_address(token0),
                        Web3.to_checksum_address(token1),
                        fee
                    ).call()
                    
                    if pool_address != '0x0000000000000000000000000000000000000000':
                        # Get token symbols
                        token0_contract = self.w3_bsc.eth.contract(
                            address=Web3.to_checksum_address(token0), 
                            abi=ERC20_ABI
                        )
                        token1_contract = self.w3_bsc.eth.contract(
                            address=Web3.to_checksum_address(token1), 
                            abi=ERC20_ABI
                        )
                        
                        symbol0 = token0_contract.functions.symbol().call()
                        symbol1 = token1_contract.functions.symbol().call()
                        
                        pair = TokenPair(
                            address=pool_address,
                            token0=token0,
                            token0_symbol=symbol0,
                            token1=token1,
                            token1_symbol=symbol1,
                            dex='pancakeswap',
                            chain='bsc',
                            fee_tier=fee
                        )
                        pairs.append(pair)
                        logger.info(f"Added pair: {pair}")
                        
                except Exception as e:
                    logger.warning(f"Failed to load pair {token0}/{token1}: {e}")
        
        self.monitored_pairs = pairs
        logger.info(f"{Fore.GREEN}Loaded {len(pairs)} pairs to monitor{Style.RESET_ALL}")
        return pairs
    
    def get_pool_price(self, pair: TokenPair) -> Optional[float]:
        """Get current price from a Uniswap V3 pool"""
        try:
            w3 = self.w3_eth if pair.chain == 'ethereum' else self.w3_bsc
            pool_contract = w3.eth.contract(
                address=Web3.to_checksum_address(pair.address),
                abi=UNISWAP_V3_POOL_ABI
            )
            
            # Get slot0 data
            slot0 = pool_contract.functions.slot0().call()
            sqrt_price_x96 = slot0[0]
            
            # Calculate price from sqrtPriceX96
            # price = (sqrt_price_x96 / 2^96)^2
            price = (sqrt_price_x96 / (2 ** 96)) ** 2
            
            # Adjust for token decimals
            token0_contract = w3.eth.contract(address=Web3.to_checksum_address(pair.token0), abi=ERC20_ABI)
            token1_contract = w3.eth.contract(address=Web3.to_checksum_address(pair.token1), abi=ERC20_ABI)
            
            decimals0 = token0_contract.functions.decimals().call()
            decimals1 = token1_contract.functions.decimals().call()
            
            # Price is token1/token0, adjust for decimals
            price_adjusted = price * (10 ** (decimals0 - decimals1))
            
            return price_adjusted
            
        except Exception as e:
            logger.warning(f"Failed to get price for {pair}: {e}")
            return None
    
    def get_pool_liquidity(self, pair: TokenPair) -> float:
        """Get pool liquidity"""
        try:
            w3 = self.w3_eth if pair.chain == 'ethereum' else self.w3_bsc
            pool_contract = w3.eth.contract(
                address=Web3.to_checksum_address(pair.address),
                abi=UNISWAP_V3_POOL_ABI
            )
            
            liquidity = pool_contract.functions.liquidity().call()
            return float(liquidity)
            
        except Exception as e:
            logger.warning(f"Failed to get liquidity for {pair}: {e}")
            return 0.0
    
    def fetch_pair_data(self, pair: TokenPair) -> Optional[PriceData]:
        """Fetch current price and data for a pair"""
        price = self.get_pool_price(pair)
        if price is None:
            return None
            
        liquidity = self.get_pool_liquidity(pair)
        
        # Estimate 24h volume (simplified - in production, use subgraph)
        volume_24h = liquidity * 0.1  # Rough estimate
        
        return PriceData(
            pair=pair,
            price=price,
            timestamp=datetime.now(),
            volume_24h=volume_24h,
            liquidity=liquidity
        )
    
    def check_opportunities(self) -> List[Opportunity]:
        """Check for scalping opportunities"""
        opportunities = []
        
        for pair in self.monitored_pairs:
            current_data = self.fetch_pair_data(pair)
            if current_data is None:
                continue
                
            pair_key = f"{pair.dex}:{pair.address}"
            
            # Store price history
            self.price_history[pair_key].append(current_data)
            
            # Keep only last 60 minutes of data
            cutoff = datetime.now() - timedelta(minutes=60)
            self.price_history[pair_key] = [
                p for p in self.price_history[pair_key] 
                if p.timestamp > cutoff
            ]
            
            # Check for price change in last minute
            one_min_ago = datetime.now() - timedelta(minutes=1)
            old_data = None
            for p in self.price_history[pair_key]:
                if p.timestamp <= one_min_ago:
                    old_data = p
                    break
            
            if old_data:
                price_change_pct = ((current_data.price - old_data.price) / old_data.price) * 100
                
                # Calculate gas costs
                gas_fee_native, gas_fee_usd = self.calculate_gas_cost(pair.chain)
                
                # Calculate potential profit
                trade_amount = config.TRADE_AMOUNT_USD
                potential_profit = trade_amount * (abs(price_change_pct) / 100)
                
                # Calculate ROI after fees (assuming we capture 50% of the move)
                capture_ratio = 0.5
                captured_profit = potential_profit * capture_ratio
                roi_after_fees = ((captured_profit - gas_fee_usd) / trade_amount) * 100
                
                # Check if opportunity is viable
                is_viable = (
                    abs(price_change_pct) >= config.PRICE_CHANGE_THRESHOLD and
                    roi_after_fees >= config.MIN_ROI_THRESHOLD
                )
                
                opportunity = Opportunity(
                    pair=pair,
                    price_change_pct=price_change_pct,
                    price_old=old_data.price,
                    price_new=current_data.price,
                    volume_24h=current_data.volume_24h,
                    liquidity=current_data.liquidity,
                    gas_fee_eth=gas_fee_native if pair.chain == 'ethereum' else 0,
                    gas_fee_usd=gas_fee_usd,
                    potential_profit_usd=potential_profit,
                    roi_after_fees=roi_after_fees,
                    timestamp=datetime.now(),
                    is_viable=is_viable
                )
                
                opportunities.append(opportunity)
                
                if is_viable:
                    self.opportunity_history.append(opportunity)
                    self.trigger_alert(opportunity)
        
        return opportunities
    
    def trigger_alert(self, opportunity: Opportunity):
        """Trigger an alert for a viable opportunity"""
        pair_key = f"{opportunity.pair.dex}:{opportunity.pair.address}"
        
        # Check cooldown
        now = datetime.now()
        if pair_key in self.alert_cooldowns:
            time_since_last = (now - self.alert_cooldowns[pair_key]).total_seconds()
            if time_since_last < config.ALERT_COOLDOWN:
                return
        
        self.alert_cooldowns[pair_key] = now
        
        # Print alert
        print("\n")
        print(f"{Back.GREEN}{Fore.BLACK}{'='*80}{Style.RESET_ALL}")
        print(f"{Back.GREEN}{Fore.BLACK}🚨 SCALPING OPPORTUNITY DETECTED!{Style.RESET_ALL}")
        print(f"{Back.GREEN}{Fore.BLACK}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Pair:{Style.RESET_ALL} {opportunity.pair}")
        print(f"{Fore.CYAN}Price Change:{Style.RESET_ALL} {Fore.RED if opportunity.price_change_pct > 0 else Fore.GREEN}{opportunity.price_change_pct:+.2f}%{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Volume 24h:{Style.RESET_ALL} ${opportunity.volume_24h:,.2f}")
        print(f"{Fore.CYAN}Liquidity:{Style.RESET_ALL} {opportunity.liquidity:,.0f}")
        print(f"{Fore.CYAN}Gas Fee:{Style.RESET_ALL} ${opportunity.gas_fee_usd:.2f}")
        print(f"{Fore.CYAN}Potential Profit:{Style.RESET_ALL} ${opportunity.potential_profit_usd:.2f}")
        print(f"{Fore.YELLOW}ROI after fees: {opportunity.roi_after_fees:.2f}%{Style.RESET_ALL}")
        print(f"{Back.GREEN}{Fore.BLACK}{'='*80}{Style.RESET_ALL}")
        
        # Sound alert
        if config.ENABLE_CONSOLE_ALERTS:
            print('\a')  # Bell character
            
        logger.info(f"ALERT: Viable opportunity detected - {opportunity.pair} - ROI: {opportunity.roi_after_fees:.2f}%")
    
    def display_opportunities(self, opportunities: List[Opportunity]):
        """Display opportunities in a table"""
        if not opportunities:
            return
            
        # Sort by absolute price change
        sorted_opps = sorted(opportunities, key=lambda x: abs(x.price_change_pct), reverse=True)
        
        table_data = []
        for opp in sorted_opps:
            change_color = Fore.RED if opp.price_change_pct > 0 else Fore.GREEN if opp.price_change_pct < 0 else Fore.WHITE
            viable_marker = f"{Back.GREEN}{Fore.BLACK} ✓ VIABLE {Style.RESET_ALL}" if opp.is_viable else ""
            
            table_data.append([
                str(opp.pair),
                f"{change_color}{opp.price_change_pct:+.2f}%{Style.RESET_ALL}",
                f"${opp.volume_24h:,.0f}",
                f"${opp.gas_fee_usd:.2f}",
                f"{opp.roi_after_fees:.1f}%",
                viable_marker
            ])
        
        headers = ['Pair', 'Change (1m)', 'Volume 24h', 'Gas Fee', 'ROI', 'Status']
        print("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def save_history(self):
        """Save opportunity history to CSV"""
        if not self.opportunity_history:
            return
            
        os.makedirs(os.path.dirname(config.HISTORY_FILE) if config.HISTORY_FILE else "data", exist_ok=True)
        
        # Convert to DataFrame
        data = [opp.to_dict() for opp in self.opportunity_history]
        df = pd.DataFrame(data)
        
        # Append to existing file if exists
        if os.path.exists(config.HISTORY_FILE):
            existing_df = pd.read_csv(config.HISTORY_FILE)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        # Remove duplicates and old data
        df = df.drop_duplicates(subset=['timestamp', 'pair'])
        cutoff = datetime.now() - timedelta(days=config.HISTORY_RETENTION_DAYS)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[df['timestamp'] > cutoff]
        
        df.to_csv(config.HISTORY_FILE, index=False)
        logger.info(f"Saved {len(df)} opportunities to {config.HISTORY_FILE}")
    
    def run(self):
        """Main monitoring loop"""
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  DEX Scalping Monitor v1.0{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  Monitoring Uniswap V3 & PancakeSwap{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # Connect to networks
        if not self.connect():
            logger.error("Failed to connect to any network. Exiting.")
            return
        
        # Fetch initial prices
        self.fetch_eth_price()
        
        # Load pairs to monitor
        self.load_popular_pairs()
        
        if not self.monitored_pairs:
            logger.error("No pairs loaded. Check your RPC connections.")
            return
        
        print(f"\n{Fore.GREEN}Starting monitoring loop...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Price change threshold: {config.PRICE_CHANGE_THRESHOLD}%{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Min ROI threshold: {config.MIN_ROI_THRESHOLD}%{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Monitoring interval: {config.MONITOR_INTERVAL}s{Style.RESET_ALL}\n")
        
        try:
            while True:
                print(f"\n{Fore.CYAN}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning for opportunities...{Style.RESET_ALL}")
                
                # Refresh ETH/BNB price every 5 minutes
                if datetime.now().minute % 5 == 0:
                    self.fetch_eth_price()
                
                # Check for opportunities
                opportunities = self.check_opportunities()
                
                # Display results
                self.display_opportunities(opportunities)
                
                # Save history periodically
                if len(self.opportunity_history) > 0 and len(self.opportunity_history) % 10 == 0:
                    self.save_history()
                
                # Count viable opportunities
                viable_count = sum(1 for o in opportunities if o.is_viable)
                if viable_count > 0:
                    print(f"{Fore.GREEN}Found {viable_count} viable opportunities!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}No viable opportunities detected. Monitoring...{Style.RESET_ALL}")
                
                # Wait for next iteration
                time.sleep(config.MONITOR_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Stopping monitor...{Style.RESET_ALL}")
            self.save_history()
            print(f"{Fore.GREEN}History saved. Goodbye!{Style.RESET_ALL}")

# ============================================
# DEMO MODE
# ============================================

def run_demo():
    """Run in demo mode with simulated data"""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  DEX Scalping Monitor - DEMO MODE{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Running with simulated data (no blockchain connection required){Style.RESET_ALL}\n")
    
    # Simulate opportunities
    demo_pairs = [
        TokenPair("0x1", "0xa", "WETH", "0xb", "USDC", "uniswap", "ethereum", 500),
        TokenPair("0x2", "0xc", "PEPE", "0xa", "WETH", "uniswap", "ethereum", 3000),
        TokenPair("0x3", "0xd", "SHIB", "0xa", "WETH", "uniswap", "ethereum", 3000),
    ]
    
    print(f"{Fore.GREEN}Simulating price movements...{Style.RESET_ALL}\n")
    
    # Demo alert
    demo_opportunity = Opportunity(
        pair=demo_pairs[1],
        price_change_pct=8.5,
        price_old=0.000001,
        price_new=0.000001085,
        volume_24h=5000000,
        liquidity=2500000,
        gas_fee_eth=0.005,
        gas_fee_usd=15.0,
        potential_profit_usd=85.0,
        roi_after_fees=7.0,
        timestamp=datetime.now(),
        is_viable=True
    )
    
    # Simulate alert display
    print(f"{Back.GREEN}{Fore.BLACK}{'='*80}{Style.RESET_ALL}")
    print(f"{Back.GREEN}{Fore.BLACK}🚨 SCALPING OPPORTUNITY DETECTED!{Style.RESET_ALL}")
    print(f"{Back.GREEN}{Fore.BLACK}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Pair:{Style.RESET_ALL} {demo_opportunity.pair}")
    print(f"{Fore.CYAN}Price Change:{Style.RESET_ALL} {Fore.RED}+{demo_opportunity.price_change_pct:.2f}%{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Volume 24h:{Style.RESET_ALL} ${demo_opportunity.volume_24h:,.2f}")
    print(f"{Fore.CYAN}Liquidity:{Style.RESET_ALL} {demo_opportunity.liquidity:,.0f}")
    print(f"{Fore.CYAN}Gas Fee:{Style.RESET_ALL} ${demo_opportunity.gas_fee_usd:.2f}")
    print(f"{Fore.CYAN}Potential Profit:{Style.RESET_ALL} ${demo_opportunity.potential_profit_usd:.2f}")
    print(f"{Fore.YELLOW}ROI after fees: {demo_opportunity.roi_after_fees:.2f}%{Style.RESET_ALL}")
    print(f"{Back.GREEN}{Fore.BLACK}{'='*80}{Style.RESET_ALL}\n")
    
    # Demo table
    table_data = [
        ["WETH/USDC", f"{Fore.GREEN}-2.3%{Style.RESET_ALL}", "$125M", "$12.50", "-1.2%", ""],
        [f"{Fore.YELLOW}PEPE/WETH{Style.RESET_ALL}", f"{Fore.RED}+8.5%{Style.RESET_ALL}", "$5M", "$15.00", f"{Fore.GREEN}+7.0%{Style.RESET_ALL}", f"{Back.GREEN}{Fore.BLACK} ✓ VIABLE {Style.RESET_ALL}"],
        ["SHIB/WETH", f"{Fore.GREEN}-1.2%{Style.RESET_ALL}", "$8M", "$14.20", "-0.5%", ""],
    ]
    
    headers = ['Pair', 'Change (1m)', 'Volume 24h', 'Gas Fee', 'ROI', 'Status']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    print(f"\n{Fore.CYAN}Demo complete! To run with real data:{Style.RESET_ALL}")
    print(f"  1. Copy .env.example to .env")
    print(f"  2. Add your Alchemy/Infura API key")
    print(f"  3. Run: python dex_monitor.py")

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='DEX Scalping Monitor')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode with simulated data')
    args = parser.parse_args()
    
    if args.demo:
        run_demo()
    else:
        monitor = DEXMonitor()
        monitor.run()
