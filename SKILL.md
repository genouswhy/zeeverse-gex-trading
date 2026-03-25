---
name: zeeverse-gex-trading
description: |
  Zeeverse GEX Trading Assistant — complete in-game trading, liquidity management, and price query functionality.

  **Core Features**:
  - 🏷️ Query item prices, pool status, and price charts
  - 💱 Execute buy/sell trades (VEE <-> items)
  - 💧 Manage liquidity (add/remove LP)
  - 👛 View account info, item inventory, and VEE balance

  **Use Cases**:
  - User asks "what is the price of an item"
  - User wants to "buy an item" or "sell an item"
  - User needs to "provide liquidity" to earn fees
  - User needs to "view price trends" or "recent trades"
  - User wants to "analyze item liquidity" or "calculate slippage"

  **Authentication**:
  Requires auth before any operation. Recommended: obtain a temporary access token from the browser (Network tab → Authorization header) and pass it to the AI. Email+password also works but carries security risks in some AI environments.

compatibility: |
  - Python 3.8+
  - requests library
  - curl (optional)
---

## Overview

Zeeverse GEX (in-game exchange) is a DEX based on the AMM (Automated Market Maker) model. This skill provides a complete Python API wrapper and interactive tools, allowing you to:
- Quickly query prices and trade data
- Automate trading and liquidity management
- Analyze price trends and trading opportunities
- Optimize slippage protection

## Authentication

Before using any feature of this skill, you must authenticate. Two methods are supported.

### Method A: Email + Password (less recommended)

You can tell the AI your email and password directly, and it will call the login API on your behalf.

**Risks and caveats:**
- Sharing credentials with an AI carries inherent security risk.
- In newer versions of OpenClaw, the AI may refuse to handle raw passwords as a safety policy.
- Claude Code (the CLI) is more likely to accept this flow.
- If you do use this method, make sure you are in a trusted, private session.

### Method B: Access Token (recommended)

Obtain a temporary access token from your browser and pass it directly to the AI. This is safer because:
- The token expires within ~24 hours, so leaking it carries limited risk.
- No password is ever shared.
- The AI simply initialises the client with `ZeeVerseGEX(access_token="eyJ...")`.

**Downside**: When the token expires you need to get a new one and tell the AI again.

#### How to get your access token from the browser

1. Open [https://www.zee-verse.com](https://www.zee-verse.com) in Chrome or Edge and log in to your account.
2. Open DevTools — press **F12** (Windows) or **Cmd+Option+I** (Mac).
3. Click the **Network** tab.
4. Refresh the page (F5), or perform any in-game action so that API calls appear.
5. In the filter bar, type `api.zee-verse.com` to narrow results.
6. Click on any request (e.g. one to `/v2/inventory` or `/v2/offchain-gex/pools`).
7. In the **Request Headers** panel, find the `Authorization` header. Its value looks like:
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
8. Copy everything **after** `Bearer ` — that is your access token.
9. Paste it to the AI: _"My access token is eyJ..."_

> Alternatively, check **Application → Local Storage → https://www.zee-verse.com** — the token may be stored under a key like `accessToken` or `auth`.

### Token expiry and refresh

Access tokens expire after approximately 24 hours. If the AI gets a `INVALID_TOKEN` error mid-session, you need to provide a fresh token (repeat the steps above). The skill also supports a `refresh_token` flow internally, but this requires the refresh token, which is harder to extract.

---

## Quick Start

### 1. Query Prices
```python
# Get all trading pools
pools = client.get_pools()

# Query price for a specific item
price = client.get_item_price(item_id="2100920016")  # Snorker

# View recent trades
trades = client.get_recent_trades(item_id="2100920016")

# Get price chart (candlesticks)
candles = client.get_candles(item_id="2100920016", interval="1h")
```

### 3. Execute Trades
```python
# Buy item
result = client.swap_vee_for_items(
    item_id="2100920016",
    item_amount=1.0,  # quantity to buy
    max_vee_amount=2.6,  # max VEE to spend (slippage protection)
)

# Sell item
result = client.swap_items_for_vee(
    item_id="2100920016",
    item_amount=1.0,  # quantity to sell
    min_vee_amount=2.4,  # min VEE to receive (slippage protection)
)
```

### 4. Liquidity Management
```python
# View liquidity positions
positions = client.get_liquidity_positions()

# Preview adding liquidity
quote = client.quote_add_liquidity(
    item_id="2100920016",
    item_amount=1.0
)
print(f"Required VEE: {quote['required_vee_amount']}")
print(f"LP tokens to receive: {quote['lp_tokens_to_receive']}")

# Add liquidity
result = client.add_liquidity(
    item_id="2100920016",
    item_amount=1.0,
    max_vee_amount=2.6  # slippage protection
)

# Remove liquidity
result = client.remove_liquidity(
    item_id="2100920016",
    lp_tokens=1.0
)
```

### 5. Account Information
```python
# VEE balance
balance = client.get_vee_balance()

# Item inventory
inventory = client.get_inventory()

# VEE price (USD)
vee_price = client.get_vee_price()
```

## API Reference

### Core Class: ZeeVerseGEX

#### Authentication Methods
- `login(email, password)` - Login and get token
- `refresh_token()` - Refresh access token (call before expiry)

#### Query Methods (no transaction signing required)
| Method | Description |
|--------|-------------|
| `get_pools()` | Returns all trading pools including VEE/item reserves |
| `get_item_price(item_id)` | Calculates current VEE price of an item |
| `get_recent_trades(item_id)` | Gets ~250 most recent trades |
| `get_candles(item_id, interval)` | Gets candlestick data (1h/1d) |
| `get_vee_price()` | Gets VEE USD price across multiple timeframes |
| `get_inventory()` | Returns account item list |
| `get_vee_balance()` | Returns VEE balance |
| `get_liquidity_positions()` | Returns your LP positions |

#### Trade Methods (require authentication)
| Method | Description | Parameters |
|--------|-------------|-----------|
| `swap_vee_for_items(item_id, item_amount, max_vee_amount)` | Buy items | item_id: item ID; item_amount: quantity to buy; max_vee_amount: max spend (slippage protection) |
| `swap_items_for_vee(item_id, item_amount, min_vee_amount)` | Sell items | item_id: item ID; item_amount: quantity to sell; min_vee_amount: min receive (slippage protection) |

#### Liquidity Methods
| Method | Description |
|--------|-------------|
| `quote_add_liquidity(item_id, item_amount)` | Preview adding liquidity (does not execute) |
| `quote_remove_liquidity(item_id, lp_tokens)` | Preview removing liquidity (does not execute) |
| `add_liquidity(item_id, item_amount, max_vee_amount)` | Add liquidity and execute |
| `remove_liquidity(item_id, lp_tokens)` | Remove liquidity and execute |

## Key Concepts

### Wei and Decimals
All on-chain data is stored in **wei** format (18 decimal places):
```python
# Conversion
human_readable = wei_amount / 1e18
wei = human_readable * 1e18
```

### Slippage Protection
You must set `maxVeeAmount` or `minVeeAmount` when trading to prevent bad fills:
```python
# Buying
calculated_cost = 2.5  # VEE
max_vee = calculated_cost * 1.03  # allow 3% slippage

# Selling
calculated_receive = 2.4  # VEE
min_vee = calculated_receive * 0.97  # allow 3% slippage
```

### AMM Pricing Formula
GEX uses the Constant Product model:
```
New price = reserve_vee / reserve_items

Buy cost formula:
vee_cost = (reserve_vee × item_amount) / ((reserve_items - item_amount) × (1 - fee_pct))

Sell return formula:
vee_received = ((item_amount × (1 - fee_pct)) × reserve_vee) / (reserve_items + item_amount × (1 - fee_pct))
```

### Current Fees
- **Protocol fee**: 2.5% (goes to protocol)
- **LP fee**: 0% (currently 0, but check pool data for latest)
- **Total fee**: ~2.5%

## Common Item IDs

| Item | ID |
|------|----|
| Snorker | 2100920016 |
| Glooper | 2100920004 |
| Snork | 2100920012 |
| Gloop | 2100920002 |
| Luminara Surge | 2100920008 |
| Energy Potion | 2101020001 |
| Full list | GET /v2/offchain-gex/pools |

## Error Handling

All methods return structured responses:
```python
response = {
    "success": bool,
    "data": {...},  # present on success
    "error": "Error message",  # present on failure
    "error_code": "NOT_FOUND"  # error code
}
```

Common errors:
- `INVALID_TOKEN` - Token expired or invalid, re-login required
- `INSUFFICIENT_BALANCE` - Insufficient VEE or item balance
- `INSUFFICIENT_LIQUIDITY` - Pool liquidity too low to execute
- `SLIPPAGE_EXCEEDED` - Actual price exceeded your slippage limit

## Scripts and Tools

### scripts/gex_client.py
Core Python client. Contains wrappers for all API methods.

**Usage**:
```python
from scripts.gex_client import ZeeVerseGEX

client = ZeeVerseGEX()
client.login(email="...", password="...")
pools = client.get_pools()
```

### scripts/quick_price.py
Quick item price query (no token saving required).

**Usage**:
```bash
python scripts/quick_price.py --item-id 2100920016 --email you@example.com --password secret
```

### scripts/execute_trade.py
One-click trade script.

**Usage**:
```bash
# Buy 1 Snorker, max spend 2.6 VEE
python scripts/execute_trade.py --action buy --item-id 2100920016 --amount 1.0 --max-vee 2.6

# Sell 1 Snorker, min receive 2.4 VEE
python scripts/execute_trade.py --action sell --item-id 2100920016 --amount 1.0 --min-vee 2.4
```

### scripts/monitor_price.py
Continuous price monitoring.

**Usage**:
```bash
python scripts/monitor_price.py --item-id 2100920016 --interval 5 --email you@example.com --password secret
```

## ✅ Delivery Checklist

### Must Verify (check each item after execution)
- [ ] API connection successful (can obtain token)?
- [ ] Pool data returned correctly (includes reserve0/reserve1/fee)?
- [ ] Price calculation accurate (matches website display)?
- [ ] Trades correctly signed and broadcast (test environment)?
- [ ] Error handling complete (token expired, insufficient balance, slippage exceeded, etc.)?

### When Issues Found (required actions)
- Stop immediately
- State clearly: what failed / error message / what was produced / what was not
- Do not continue pretending "success"

## License and Disclaimer

⚠️ **Important**:
- This skill is based on the public Zeeverse GEX API
- Trading involves real asset risk — use with caution
- Always test slippage protection parameters to prevent bad fills
- Refresh tokens regularly to prevent expiry-related trade interruptions

Happy trading! 🚀
