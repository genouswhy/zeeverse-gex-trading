#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-click trade script.
Supports buy/sell with slippage protection.
Auth: --access-token (saved to .env) > .env > --email/--password.
"""

import argparse
import sys
import os
import io
from gex_client import ZeeVerseGEX

# Handle Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# .env path: one level up from this script (skill root)
_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")


def _load_env():
    """Load .env file into os.environ (only sets if not already set)."""
    if os.path.exists(_ENV_PATH):
        with open(_ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def _save_token(token: str):
    """Persist token to .env, replacing any existing ZEEVERSE_ACCESS_TOKEN line."""
    lines = []
    if os.path.exists(_ENV_PATH):
        with open(_ENV_PATH) as f:
            lines = [l for l in f if not l.startswith("ZEEVERSE_ACCESS_TOKEN=")]
    lines.append(f"ZEEVERSE_ACCESS_TOKEN={token}\n")
    with open(_ENV_PATH, "w") as f:
        f.writelines(lines)
    print("Token saved to .env", file=sys.stderr)


def _build_client(args) -> ZeeVerseGEX:
    """Resolve auth: --access-token > .env > --email/--password."""
    client = ZeeVerseGEX()

    token = getattr(args, "access_token", None)
    if token:
        client.access_token = token
        client._update_headers()
        _save_token(token)
        return client

    env_token = os.environ.get("ZEEVERSE_ACCESS_TOKEN")
    if env_token:
        print("Using token from .env", file=sys.stderr)
        client.access_token = env_token
        client._update_headers()
        return client

    email = getattr(args, "email", None)
    password = getattr(args, "password", None)
    if email and password:
        print("Logging in... ", end="", file=sys.stderr)
        result = client.login(email, password)
        if not result["success"]:
            print(f"❌ Login failed: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print("✅", file=sys.stderr)
        if client.access_token:
            _save_token(str(client.access_token))
        return client

    print(
        "❌ No auth provided. Use one of:\n"
        "  --access-token eyJ...\n"
        "  --email EMAIL --password PASSWORD\n"
        "  (or set ZEEVERSE_ACCESS_TOKEN in .env)",
        file=sys.stderr,
    )
    sys.exit(1)


def main():
    _load_env()

    parser = argparse.ArgumentParser(description="Zeeverse GEX trading")
    parser.add_argument("--action", choices=["buy", "sell"], required=True, help="Action type: buy or sell")
    parser.add_argument("--item-id", required=True, help="Item ID")
    parser.add_argument("--amount", type=float, required=True, help="Trade amount")
    parser.add_argument("--access-token", help="Zeeverse access token (saved to .env for reuse)")
    parser.add_argument("--email", help="Account email")
    parser.add_argument("--password", help="Account password")
    parser.add_argument("--max-vee", type=float, help="Max VEE for buy (slippage protection)")
    parser.add_argument("--min-vee", type=float, help="Min VEE for sell (slippage protection)")
    parser.add_argument("--slippage", type=float, default=0.03, help="Default slippage (default 3 percent)")
    parser.add_argument("--skip-confirm", action="store_true", help="Skip confirmation")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    client = _build_client(args)

    # Calculate slippage protection params
    if args.action == "buy":
        if args.max_vee is None:
            buy_cost = client.calculate_buy_cost(args.item_id, args.amount)
            if not buy_cost:
                print(f"❌ Unable to calculate buy cost", file=sys.stderr)
                sys.exit(1)
            calculated_cost = buy_cost["total"]
            max_vee = calculated_cost * (1 + args.slippage)
        else:
            max_vee = args.max_vee
            calculated_cost = max_vee / (1 + args.slippage)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"🛒 Buy Confirmation", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Item ID: {args.item_id}", file=sys.stderr)
        print(f"Amount: {args.amount}", file=sys.stderr)
        print(f"Expected cost: {calculated_cost:.6f} VEE", file=sys.stderr)
        print(f"Max cost (with slippage): {max_vee:.6f} VEE", file=sys.stderr)
        print(f"Slippage limit: {args.slippage*100:.2f}%", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        if not args.skip_confirm:
            response = input("Confirm trade? (y/n): ")
            if response.lower() != "y":
                print("❌ Trade cancelled", file=sys.stderr)
                sys.exit(0)

        print(f"Executing buy... ", end="", file=sys.stderr)
        result = client.swap_vee_for_items(args.item_id, args.amount, max_vee)

    else:  # sell
        if args.min_vee is None:
            sell_return = client.calculate_sell_return(args.item_id, args.amount)
            if not sell_return:
                print(f"❌ Unable to calculate sell return", file=sys.stderr)
                sys.exit(1)
            calculated_return = sell_return["net"]
            min_vee = calculated_return * (1 - args.slippage)
        else:
            min_vee = args.min_vee
            calculated_return = min_vee / (1 - args.slippage)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"💳 Sell Confirmation", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Item ID: {args.item_id}", file=sys.stderr)
        print(f"Amount: {args.amount}", file=sys.stderr)
        print(f"Expected return: {calculated_return:.6f} VEE", file=sys.stderr)
        print(f"Min return (with slippage): {min_vee:.6f} VEE", file=sys.stderr)
        print(f"Slippage limit: {args.slippage*100:.2f}%", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        if not args.skip_confirm:
            response = input("Confirm trade? (y/n): ")
            if response.lower() != "y":
                print("❌ Trade cancelled", file=sys.stderr)
                sys.exit(0)

        print(f"Executing sell... ", end="", file=sys.stderr)
        result = client.swap_items_for_vee(args.item_id, args.amount, min_vee)

    # Handle result
    if result["success"]:
        print("✅", file=sys.stderr)
        print(f"\n✅ Trade successful!", file=sys.stderr)
        if args.json:
            import json
            print(json.dumps(result, indent=2))
        else:
            print(f"New reserve data:")
            print(f"  VEE: {result['data'].get('newVeeReserve', 'N/A')}")
            print(f"  Items: {result['data'].get('newItemReserve', 'N/A')}", file=sys.stderr)
    else:
        print("❌", file=sys.stderr)
        if result.get("error_code") == "INVALID_TOKEN":
            print(f"\n❌ Token expired. Re-run with --access-token eyJ...", file=sys.stderr)
        else:
            print(f"\n❌ Trade failed: {result['error']}", file=sys.stderr)
            if result.get('error_code'):
                print(f"Error code: {result['error_code']}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
