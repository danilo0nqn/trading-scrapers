# Popular DEX Pairs for Monitoring
# ================================
# This file contains popular token pairs for scalping opportunities.
# Add these addresses to your monitoring configuration.

## Uniswap V3 (Ethereum)

### Major Pairs
| Pair | Pool Address | Fee Tier | Notes |
|------|-------------|----------|-------|
| WETH/USDC | 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8 | 0.05% | Most liquid pair |
| WETH/USDT | 0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36 | 0.05% | High volume |
| USDC/USDT | 0x3416cF6C708Da44DB2624D63ea0AAef7113527C6 | 0.01% | Stable pair |
| WBTC/WETH | 0xCBCdF9626bC03E24f779434178A73a0B4bad62eD | 0.05% | BTC exposure |

### Altcoin Pairs (Higher Volatility)
| Pair | Token0 | Token1 | Notes |
|------|--------|--------|-------|
| PEPE/WETH | 0x6982508145454Ce325dDbE47a25d4ec3d2311933 | WETH | Meme coin |
| SHIB/WETH | 0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE | WETH | Meme coin |
| DOGE/WETH | 0x4206931337dc273a630d328dA6441786BfaD668f | WETH | Bridged DOGE |
| UNI/WETH | 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984 | WETH | DEX token |
| LINK/WETH | 0x514910771AF9Ca656af840dff83E8264EcF986CA | WETH | Oracle token |
| AAVE/WETH | 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9 | WETH | DeFi token |
| MKR/WETH | 0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2 | WETH | DeFi token |
| LDO/WETH | 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32 | WETH | Liquid staking |

## PancakeSwap V3 (BSC)

### Major Pairs
| Pair | Pool Address | Fee Tier | Notes |
|------|-------------|----------|-------|
| WBNB/BUSD | 0x36696169C63e42cd08ce11f5deeBbCeBae652050 | 0.25% | Primary pair |
| WBNB/USDT | 0x172fcD41E0913e95784454622d1c3724f546f849 | 0.25% | High volume |
| CAKE/WBNB | 0x133B3D95bAD5405d14d53473671200e9342896BF | 0.25% | DEX token |
| ETH/WBNB | 0xD0e226f674bBf064f54aB47F42473fF80DB98CBA | 0.25% | Cross-chain |

### BSC Altcoin Pairs
| Pair | Token0 | Token1 | Notes |
|------|--------|--------|-------|
| SAFEMOON/WBNB | 0x42981d0bfbAf196529376EE702F2a9Eb9092fcB5 | WBNB | High volatility |
| BABYDOGE/WBNB | 0xc748673057861a797275CD8A068AbB95A902e8de | WBNB | Meme coin |
| FLOKI/WBNB | 0xfb5B838b6cfEEdC2873aB27866079AC55363D37E | WBNB | Meme coin |

## Token Addresses Reference

### Ethereum Mainnet
| Token | Address | Decimals |
|-------|---------|----------|
| WETH | 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 | 18 |
| USDC | 0xA0b86a33E6441e0A421e56E4773C3C4b0Db7E5e0 | 6 |
| USDT | 0xdAC17F958D2ee523a2206206994597C13D831ec7 | 6 |
| WBTC | 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599 | 8 |
| DAI | 0x6B175474E89094C44Da98b954EedeAC495271d0F | 18 |

### BSC Mainnet
| Token | Address | Decimals |
|-------|---------|----------|
| WBNB | 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c | 18 |
| BUSD | 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56 | 18 |
| USDT | 0x55d398326f99059fF775485246999027B3197955 | 18 |
| USDC | 0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d | 18 |
| CAKE | 0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82 | 18 |
| ETH | 0x2170Ed0880ac9A755fd29B2688956BD959F933F8 | 18 |

## How to Add New Pairs

1. Find the pool contract address on:
   - Uniswap: https://info.uniswap.org
   - PancakeSwap: https://pancakeswap.finance/info

2. Verify the pool has:
   - Sufficient liquidity (> $100k recommended)
   - Regular trading volume
   - Reasonable gas costs for entry/exit

3. Add to config.py or pass to the monitor

## Notes

- Fee tiers affect profitability calculation
- Higher fee = more slippage but less competition
- 0.05% fee = best for major pairs
- 0.3% fee = standard for altcoins
- 1.0% fee = exotic pairs
