"""
DEX Scalping Monitor - Configuration
=====================================
Copy this file to .env and fill in your API keys
"""
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """Configuration for DEX Scalping Monitor"""
    
    # ============================================
    # API KEYS - REQUIRED
    # ============================================
    
    # Ethereum (Uniswap V3) - Get from: https://www.alchemy.com or https://infura.io
    ETHEREUM_RPC_URL: str = os.getenv("ETHEREUM_RPC_URL", "https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY")
    
    # BSC (PancakeSwap) - Get from: https://www.quicknode.com or https://bsc-dataseed.binance.org/
    BSC_RPC_URL: str = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
    
    # Optional: Secondary RPC for failover
    ETHEREUM_RPC_BACKUP: Optional[str] = os.getenv("ETHEREUM_RPC_BACKUP")
    BSC_RPC_BACKUP: Optional[str] = os.getenv("BSC_RPC_BACKUP")
    
    # ============================================
    # MONITORING SETTINGS
    # ============================================
    
    # Price change threshold to trigger alert (%)
    PRICE_CHANGE_THRESHOLD: float = float(os.getenv("PRICE_CHANGE_THRESHOLD", "5.0"))
    
    # Minimum ROI to consider an opportunity viable (%)
    MIN_ROI_THRESHOLD: float = float(os.getenv("MIN_ROI_THRESHOLD", "10.0"))
    
    # Monitoring interval in seconds
    MONITOR_INTERVAL: int = int(os.getenv("MONITOR_INTERVAL", "60"))
    
    # Number of top pairs to monitor per DEX
    TOP_PAIRS_LIMIT: int = int(os.getenv("TOP_PAIRS_LIMIT", "50"))
    
    # Historical data retention (days)
    HISTORY_RETENTION_DAYS: int = int(os.getenv("HISTORY_RETENTION_DAYS", "30"))
    
    # ============================================
    # GAS SETTINGS
    # ============================================
    
    # Maximum gas price to consider (in Gwei)
    MAX_GAS_PRICE_GWEI: int = int(os.getenv("MAX_GAS_PRICE_GWEI", "100"))
    
    # Gas limit for swap transactions
    GAS_LIMIT_SWAP: int = int(os.getenv("GAS_LIMIT_SWAP", "200000"))
    
    # Trade amount for ROI calculation (in USD)
    TRADE_AMOUNT_USD: float = float(os.getenv("TRADE_AMOUNT_USD", "1000.0"))
    
    # ============================================
    # ALERT SETTINGS
    # ============================================
    
    # Enable sound alerts
    ENABLE_SOUND_ALERTS: bool = os.getenv("ENABLE_SOUND_ALERTS", "true").lower() == "true"
    
    # Enable console alerts (bell character)
    ENABLE_CONSOLE_ALERTS: bool = os.getenv("ENABLE_CONSOLE_ALERTS", "true").lower() == "true"
    
    # Minimum time between alerts for same pair (seconds)
    ALERT_COOLDOWN: int = int(os.getenv("ALERT_COOLDOWN", "300"))
    
    # ============================================
    # FILE PATHS
    # ============================================
    
    # Path to store opportunity history
    HISTORY_FILE: str = os.getenv("HISTORY_FILE", "data/opportunities_history.csv")
    
    # Path to store logs
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/dex_monitor.log")
    
    # ============================================
    # DEX CONTRACTS (Mainnet)
    # ============================================
    
    # Uniswap V3 Factory and Quoter
    UNISWAP_V3_FACTORY: str = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    UNISWAP_V3_QUOTER: str = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
    
    # PancakeSwap V3 Factory and Quoter
    PANCAKESWAP_V3_FACTORY: str = "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
    PANCAKESWAP_V3_QUOTER: str = "0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997"
    
    # WETH and major token addresses (Ethereum)
    WETH_ADDRESS: str = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    USDC_ADDRESS: str = "0xA0b86a33E6441e0A421e56E4773C3C4b0Db7E5e0"
    USDT_ADDRESS: str = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    
    # WBNB and major token addresses (BSC)
    WBNB_ADDRESS: str = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
    BUSD_ADDRESS: str = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"

# Create global config instance
config = Config()
