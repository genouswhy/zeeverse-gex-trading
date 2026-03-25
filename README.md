# Zeeverse GEX Trading Skill

**Zeeverse GEX Trading Assistant** — complete in-game trading, liquidity management, and price query functionality.

## Quick Start

### Installation
```bash
# Skill is included in the Claude Code skills directory
# No additional installation required
```

### Basic Usage

```python
from scripts.gex_client import ZeeVerseGEX

# Initialize client
client = ZeeVerseGEX()

# Login
client.login(email="your@email.com", password="password")

# Query price
price = client.get_item_price(item_id="2100920016")  # Snorker
print(f"Snorker price: {price:.6f} VEE")

# View all pools
pools = client.get_pools()

# Execute trade
result = client.swap_vee_for_items(
    item_id="2100920016",
    item_amount=1.0,
    max_vee_amount=2.6  # slippage protection
)
```

## Core Features

### 🏷️ Price and Data Queries
- `get_pools()` - Get all trading pools
- `get_item_price(item_id)` - Get price for a single item
- `get_pool_info(item_id)` - Get complete pool information
- `get_recent_trades(item_id)` - View recent trades
- `get_candles(item_id, interval)` - Candlestick data
- `get_vee_price()` - VEE USD price

### 💱 Trade Execution
- `swap_vee_for_items(item_id, item_amount, max_vee)` - Buy items
- `swap_items_for_vee(item_id, item_amount, min_vee)` - Sell items

### 💧 Liquidity Management
- `quote_add_liquidity(item_id, item_amount)` - Preview add LP
- `quote_remove_liquidity(item_id, lp_tokens)` - Preview remove LP
- `add_liquidity(item_id, item_amount, max_vee)` - Add LP
- `remove_liquidity(item_id, lp_tokens)` - Remove LP

### 👛 Account Information
- `get_inventory()` - Item inventory
- `get_vee_balance()` - VEE balance
- `get_liquidity_positions()` - LP positions

## Usage Examples

### Scenario 1: Quick Price Query
```bash
cd skills/zeeverse-gex-trading
python scripts/quick_price.py --item-id 2100920016 --email you@example.com --password secret
```

### Scenario 2: Execute Trade
```bash
# Buy 1 Snorker, max spend 2.6 VEE
python scripts/execute_trade.py \
  --action buy \
  --item-id 2100920016 \
  --amount 1.0 \
  --email you@example.com \
  --password secret \
  --max-vee 2.6

# Sell 2 Gloopers, min receive 4.8 VEE
python scripts/execute_trade.py \
  --action sell \
  --item-id 2100920004 \
  --amount 2.0 \
  --email you@example.com \
  --password secret \
  --min-vee 4.8
```

### Scenario 3: Cost Calculation and Analysis
```python
from scripts.gex_client import ZeeVerseGEX

client = ZeeVerseGEX()
client.login(email="you@example.com", password="secret")

# Query buy cost
buy_cost = client.calculate_buy_cost("2100920016", 5.0)
print(f"Buy 5 Snorkers:")
print(f"  Cost: {buy_cost['vee_cost']:.6f} VEE")
print(f"  Fee: {buy_cost['fee']:.6f} VEE ({buy_cost['fee_pct']:.2f}%)")
print(f"  Total: {buy_cost['total']:.6f} VEE")

# Query sell return
sell_return = client.calculate_sell_return("2100920016", 5.0)
print(f"Sell 5 Snorkers:")
print(f"  Gross: {sell_return['vee_received']:.6f} VEE")
print(f"  Fee: {sell_return['fee']:.6f} VEE")
print(f"  Net: {sell_return['net']:.6f} VEE")
```

## Key Concepts

### Wei Conversion
All on-chain data uses wei format (18 decimal places):
```python
# Convert
human_amount = wei_amount / 1e18
wei_amount = human_amount * 1e18
```

### Slippage Protection
You must set `maxVeeAmount` or `minVeeAmount` when trading:
```python
# Buy: expected cost × 1.03 (allow 3% slippage)
max_vee = expected_cost * 1.03

# Sell: expected return × 0.97 (allow 3% slippage)
min_vee = expected_return * 0.97
```

### AMM Pricing
GEX uses the constant product model (x × y = k):
```
price = reserve_vee / reserve_items
```

## Error Handling

All API calls return structured responses:
```python
response = {
    "success": bool,
    "data": {...},        # present on success
    "error": "...",       # present on failure
    "error_code": "..."   # error code
}

# Check result
if response["success"]:
    print("Success:", response["data"])
else:
    print("Failed:", response["error"])
```

Common error codes:
- `INVALID_TOKEN` - Token expired
- `INSUFFICIENT_BALANCE` - Insufficient balance
- `INSUFFICIENT_LIQUIDITY` - Insufficient pool liquidity
- `SLIPPAGE_EXCEEDED` - Slippage exceeded limit

## File Structure

```
zeeverse-gex-trading/
├── SKILL.md              # Skill description (main document)
├── README.md             # This file
└── scripts/
    ├── gex_client.py     # Core API client
    ├── quick_price.py    # Quick price query script
    ├── execute_trade.py  # One-click trade script
    └── tests/
        ├── __init__.py
        └── test_gex_client.py  # Integration tests
└── evals/
    └── evals.json        # Test cases
```

## References

1. Zeeverse GEX API Documentation - https://dorian-snowman-7e2.notion.site/Zeeverse-GEX-API-32e9fb802d4b80d1ba78c34da3f644d1
2. AMM Constant Product Model - https://docs.uniswap.org/protocol/concepts/V3-overview/how-swaps-work

## License

⚠️ **Disclaimer**:
- This skill is based on the public Zeeverse GEX API
- Trading involves real assets — use with caution
- Always test slippage protection to prevent bad fills
- Refresh tokens regularly to prevent expiry-related interruptions

## Feedback and Improvements

Issues or suggestions are welcome!
