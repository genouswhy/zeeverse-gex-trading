#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick item price query script.
One-shot query without saving token.
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


def main():
    parser = argparse.ArgumentParser(description="Quick query for Zeeverse item prices")
    parser.add_argument("--item-id", required=True, help="Item ID (e.g. 2100920016)")
    parser.add_argument("--email", required=True, help="Zeeverse account email")
    parser.add_argument("--password", required=True, help="Zeeverse account password")
    parser.add_argument("--amount", type=float, default=1.0, help="Quantity for cost analysis (default 1.0)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Initialize client
    client = ZeeVerseGEX()

    # Login
    print(f"Logging in... ", end="", file=sys.stderr)
    login_result = client.login(args.email, args.password)
    if not login_result["success"]:
        print(f"❌ Login failed: {login_result['error']}", file=sys.stderr)
        sys.exit(1)
    print("✅", file=sys.stderr)

    # Get pool info
    print(f"Querying item {args.item_id}... ", end="", file=sys.stderr)
    pool_result = client.get_pool_info(args.item_id)
    if not pool_result["success"]:
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
