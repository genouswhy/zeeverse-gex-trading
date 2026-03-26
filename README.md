# zeeverse-gex-trading

Zeeverse GEX trading assistant — handles price queries, buy/sell execution, and liquidity management on the in-game AMM exchange.

## When to invoke

Invoke this skill when the user says anything like:

- "What's the price of Snorker on GEX?"
- "Buy 2 Gloopers for me"
- "Sell my Energy Potions for VEE"
- "How much VEE would I get if I sold 5 Snorks?"
- "Check my GEX liquidity positions"
- "Add liquidity to the Gloop pool"
- "Show me the price chart for Luminara Surge"
- "What are the trading fees?"
- "Compare Snorker vs Gloop trading cost"

## What this skill does

### 🏷️ Price queries
Fetches live pool data and calculates current price, buy cost, sell return, and fee breakdown for any item. Can also pull recent trades and candlestick chart data.

### 💱 Trade execution
Buys or sells items with automatic slippage protection (default 3%). Always previews cost/return before executing. Requires account email + password or an existing access token.

### 💧 Liquidity management
Previews and executes add/remove liquidity operations. Shows LP token amounts and required VEE.

### 👛 Account info
Checks VEE balance, item inventory, and current LP positions.

## Scope

### This skill handles
- Any GEX price / cost / fee question
- Buy or sell trade execution (single items, any quantity)
- Liquidity add / remove / preview
- Account balance and inventory queries
- VEE USD price lookup

### This skill does NOT handle
- Cross-exchange arbitrage analysis
- Portfolio tracking across sessions
- Automated recurring trades (use a cron/loop skill for that)
- On-chain wallet operations (GEX is off-chain)

## Authentication

**Must authenticate before any operation.** Two methods are supported:

> **Recommended runtime: Claude Code (CLI).** Recent versions of OpenClaw have significantly strengthened safety guardrails — they will likely refuse to execute trades or handle credentials, leaving you with read-only price queries only. Claude Code does not have these restrictions and can run the full skill.

**Method A — Email + Password** (less recommended): Tell the AI your email and password; it will call the login API for you. Risks: sharing credentials with an AI is inherently risky. Newer versions of OpenClaw will likely refuse to handle raw passwords as a safety policy. Claude Code (the CLI) is more likely to comply.

**Method B — Access Token** (recommended): Obtain a temporary token from your browser and pass it to the AI. Safer because the token expires in ~24 hours, limiting leak exposure. Downside: you need to renew it each time it expires.

**How to get your access token from the browser:**
1. Open https://www.zee-verse.com and log in.
2. Press **F12** (Windows) or **Cmd+Option+I** (Mac) to open DevTools.
3. Click the **Network** tab, then refresh the page (F5).
4. In the filter bar, type `api.zee-verse.com`.
5. Click any request (e.g. `/v2/inventory` or `/v2/offchain-gex/pools`).
6. In **Request Headers**, find the `Authorization` header: `Bearer eyJ...`
7. Copy everything **after** `Bearer ` — that is your access token.
8. Tell the AI: _"My access token is eyJ..."_

> Alternative: **Application → Local Storage → https://www.zee-verse.com** — look for a key named `accessToken` or `auth`.

Token expires after ~24 hours. If you see `INVALID_TOKEN`, extract a fresh token from the browser and provide it again.

---

## Key behaviour

**Authentication**: Ask the user for a token or credentials if not already provided. Never store credentials.

**Slippage protection**: Always calculate expected cost/return before executing a trade. Apply 3% buffer by default (`max_vee = cost × 1.03`, `min_vee = return × 0.97`). Show the user the numbers before submitting.

**AMM pricing**: GEX uses constant product (`price = reserve_vee / reserve_items`). Larger trades move the price — always show the effective price per unit, not just the pool spot price.

**Fees**: Protocol fee is 2.5%, LP fee is 0%. Total ~2.5%.

**Wei conversion**: All API values are in wei (18 decimals). The client handles conversion automatically.

## Common item IDs

| Item | ID |
|------|----|
| Snorker | 2100920016 |
| Glooper | 2100920004 |
| Snork | 2100920012 |
| Gloop | 2100920002 |
| Luminara Surge | 2100920008 |
| Energy Potion | 2101020001 |

Full list: call `get_pools()` — each pool's `token1` field is the item ID.

## Error codes

| Code | Meaning | Action |
|------|---------|--------|
| `INVALID_TOKEN` | Token expired | Re-login |
| `INSUFFICIENT_BALANCE` | Not enough VEE or items | Check balance first |
| `INSUFFICIENT_LIQUIDITY` | Pool too small | Reduce trade size |
| `SLIPPAGE_EXCEEDED` | Price moved past limit | Widen slippage or retry |

## Running tests

```bash
cd skills/zeeverse-gex-trading/scripts
python -m pytest tests/ -v
```

34 integration tests hit the real API. All read-only by default; trade tests expect API-level rejections (no assets spent).

## References

- Zeeverse GEX API: https://dorian-snowman-7e2.notion.site/Zeeverse-GEX-API-32e9fb802d4b80d1ba78c34da3f644d1
- AMM model: https://docs.uniswap.org/protocol/concepts/V3-overview/how-swaps-work

> ⚠️ Trading involves real in-game assets. Always verify slippage parameters before execution.
