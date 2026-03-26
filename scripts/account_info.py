#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account info script — view VEE balance, item inventory, and LP positions.
Auth: --access-token (saved to .env) > .env > --email/--password.
"""

import argparse
import sys
import os
import json as _json
import io
from gex_client import ZeeVerseGEX

# Handle Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# .env path: one level up from this script (skill root)
_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")


def _load_env():
    if os.path.exists(_ENV_PATH):
        with open(_ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def _save_token(token: str):
    lines = []
    if os.path.exists(_ENV_PATH):
        with open(_ENV_PATH) as f:
            lines = [l for l in f if not l.startswith("ZEEVERSE_ACCESS_TOKEN=")]
    lines.append(f"ZEEVERSE_ACCESS_TOKEN={token}\n")
    with open(_ENV_PATH, "w") as f:
        f.writelines(lines)
    print("Token saved to .env", file=sys.stderr)


def _build_client(args) -> ZeeVerseGEX:
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


def _check(result, label: str):
    """Exit on INVALID_TOKEN, otherwise return data."""
    if not result["success"]:
        if result.get("error_code") == "INVALID_TOKEN":
            print(f"❌ Token expired. Re-run with --access-token eyJ...", file=sys.stderr)
            sys.exit(1)
        print(f"❌ {label} failed: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    return result["data"]


def main():
    _load_env()

    parser = argparse.ArgumentParser(description="View Zeeverse account info")
    parser.add_argument("--access-token", help="Zeeverse access token (saved to .env for reuse)")
    parser.add_argument("--email", help="Account email")
    parser.add_argument("--password", help="Account password")
    parser.add_argument("--balance", action="store_true", help="Show VEE balance only")
    parser.add_argument("--inventory", action="store_true", help="Show item inventory only")
    parser.add_argument("--positions", action="store_true", help="Show LP positions only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    client = _build_client(args)

    # If no specific flag, show all
    show_all = not (args.balance or args.inventory or args.positions)

    output = {}

    if show_all or args.balance:
        data = _check(client.get_vee_balance(), "VEE balance")
        output["vee_balance"] = data

    if show_all or args.inventory:
        data = _check(client.get_inventory(), "inventory")
        output["inventory"] = data

    if show_all or args.positions:
        data = _check(client.get_liquidity_positions(), "LP positions")
        output["lp_positions"] = data

    if args.json:
        print(_json.dumps(output, indent=2))
        return 0

    print("\n" + "=" * 60)
    print("👛 Account Info")
    print("=" * 60)

    if "vee_balance" in output:
        bal = output["vee_balance"]
        if isinstance(bal, dict):
            vee = bal.get("veeBalance") or bal.get("balance") or bal
            print(f"\n💰 VEE Balance: {vee}")
        else:
            print(f"\n💰 VEE Balance: {bal}")

    if "inventory" in output:
        inv = output["inventory"]
        print(f"\n🎒 Inventory ({len(inv)} item type(s)):")
        if inv:
            for item in inv:
                item_id = item.get("itemId") or item.get("id") or "?"
                amount = item.get("amount") or item.get("balance") or "?"
                name = item.get("name") or item_id
                print(f"   {name}: {amount}")
        else:
            print("   (empty)")

    if "lp_positions" in output:
        positions = output["lp_positions"]
        print(f"\n💧 LP Positions ({len(positions)} pool(s)):")
        if positions:
            for pos in positions:
                pool_id = pos.get("poolId") or pos.get("id") or "?"
                lp = pos.get("lpTokens") or pos.get("lpBalance") or pos.get("amount") or "?"
                print(f"   Pool {pool_id}: {lp} LP tokens")
        else:
            print("   (no LP positions)")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
