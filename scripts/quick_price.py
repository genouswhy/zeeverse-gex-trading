#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick item price query script.
Supports --access-token (saves to .env) or --email/--password.
Subsequent runs auto-load token from .env.
"""

import argparse
import sys
import json
import os
from gex_client import ZeeVerseGEX

# Handle Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
        _save_token(client.access_token)
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

    parser = argparse.ArgumentParser(description="Quick query for Zeeverse item prices")
    parser.add_argument("--item-id", required=True, help="Item ID (e.g. 2100920016)")
    parser.add_argument("--access-token", help="Zeeverse access token (saved to .env for reuse)")
    parser.add_argument("--email", help="Zeeverse account email")
    parser.add_argument("--password", help="Zeeverse account password")
    parser.add_argument("--amount", type=float, default=1.0, help="Quantity for cost analysis (default 1.0)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    client = _build_client(args)

    # Get pool info
    print(f"Querying item {args.item_id}... ", end="", file=sys.stderr)
    pool_result = client.get_pool_info(args.item_id)
    if not pool_result["success"]:
        if pool_result.get("error_code") == "INVALID_TOKEN":
            print(f"❌ Token expired. Re-run with --access-token eyJ...", file=sys.stderr)
        else:
            print(f"❌ {pool_result['error']}", file=sys.stderr)
        sys.exit(1)
    print("✅", file=sys.stderr)

    pool_data = pool_result["data"]
    price = pool_data["price_per_item"]

    # Calculate buy cost and sell return
    buy_cost = client.calculate_buy_cost(args.item_id, args.amount)
    sell_return = client.calculate_sell_return(args.item_id, args.amount)

    # Prepare output
    output = {
        "item_id": args.item_id,
        "current_price_vee": price,
        "pool_info": {
            "reserve_vee": pool_data["reserve_vee"],
            "reserve_items": pool_data["reserve_items"],
            "total_lp_supply": pool_data["total_lp_supply"],
            "protocol_fee_pct": pool_data["protocol_fee_pct"],
            "lp_fee_pct": pool_data["lp_fee_pct"],
            "total_fee_pct": pool_data["total_fee_pct"],
        }
    }

    if buy_cost:
        output["buy_analysis"] = {
            "amount": buy_cost["item_amount"],
            "cost_vee": buy_cost["vee_cost"],
            "fee_vee": buy_cost["fee"],
            "total_vee": buy_cost["total"],
            "fee_pct": buy_cost["fee_pct"],
            "price_per_item": buy_cost["total"] / buy_cost["item_amount"],
        }

    if sell_return:
        output["sell_analysis"] = {
            "amount": sell_return["item_amount"],
            "receive_vee": sell_return["vee_received"],
            "fee_vee": sell_return["fee"],
            "net_vee": sell_return["net"],
            "fee_pct": sell_return["fee_pct"],
            "price_per_item": sell_return["net"] / sell_return["item_amount"],
        }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print("\n" + "=" * 60)
        print(f"📊 Item ID: {args.item_id}")
        print(f"💰 Current price: {price:.6f} VEE/unit")
        print(f"📈 Pool reserves: {pool_data['reserve_vee']:.2f} VEE | {pool_data['reserve_items']:.2f} items")
        print(f"🏷️ Fee: {pool_data['total_fee_pct']*100:.2f}%")

        if buy_cost:
            print(f"\n🛒 Buy {buy_cost['item_amount']:.2f} unit(s):")
            print(f"   Cost: {buy_cost['vee_cost']:.6f} VEE")
            print(f"   Fee: {buy_cost['fee']:.6f} VEE ({buy_cost['fee_pct']:.2f}%)")
            print(f"   Total: {buy_cost['total']:.6f} VEE")
            print(f"   Price/unit: {buy_cost['total']/buy_cost['item_amount']:.6f} VEE")

        if sell_return:
            print(f"\n💳 Sell {sell_return['item_amount']:.2f} unit(s):")
            print(f"   Gross: {sell_return['vee_received']:.6f} VEE")
            print(f"   Fee: {sell_return['fee']:.6f} VEE ({sell_return['fee_pct']:.2f}%)")
            print(f"   Net: {sell_return['net']:.6f} VEE")
            print(f"   Price/unit: {sell_return['net']/sell_return['item_amount']:.6f} VEE")

        print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
