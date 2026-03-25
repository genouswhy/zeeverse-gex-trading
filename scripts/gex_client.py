"""
Zeeverse GEX Trading API Client
Complete Python wrapper supporting all trading, liquidity, and query operations.
"""

import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import time


class ZeeVerseGEX:
    """Zeeverse GEX trading client"""

    BASE_URL = "https://api.zee-verse.com"
    VERSION = "v2"

    def __init__(self, access_token: Optional[str] = None, refresh_token: Optional[str] = None):
        """
        Initialize the client.

        Args:
            access_token: Optional access token (skips login)
            refresh_token: Optional refresh token (used for token refresh)
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = None
        self.session = requests.Session()
        self._update_headers()

    def _update_headers(self):
        """Update request headers"""
        self.session.headers.update({
            "Content-Type": "application/json",
        })
        if self.access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Send an API request.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint (e.g. /v2/offchain-gex/pools)
            data: Request body (POST)
            params: Query parameters (GET)

        Returns:
            Response JSON or error response
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 401:
                return {"success": False, "error": "Unauthorized - Token invalid or expired", "error_code": "INVALID_TOKEN"}
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    return {"success": False, "error": error_data.get("message", "Bad request"), "error_code": error_data.get("code")}
                except:
                    return {"success": False, "error": "Bad request", "error_code": "BAD_REQUEST"}
            else:
                return {"success": False, "error": f"API error: {response.status_code}", "error_code": f"HTTP_{response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout", "error_code": "TIMEOUT"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection error", "error_code": "CONNECTION_ERROR"}
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "UNKNOWN"}

    # ============== Authentication ==============

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login with email and password.

        Args:
            email: Account email
            password: Account password

        Returns:
            {"success": bool, "data": {"accessToken": "...", "refreshToken": "...", "expiresAt": "..."}}
        """
        response = self._request("POST", f"/{self.VERSION}/account/login", data={
            "email": email,
            "password": password
        })

        if response["success"]:
            data = response["data"]
            self.access_token = data["accessToken"]
            self.refresh_token = data["refreshToken"]
            self.token_expiry = data["expiresAt"]
            self._update_headers()
            return {"success": True, "data": data}
        else:
            return response

    def refresh(self) -> Dict[str, Any]:
        """
        Refresh the access token.

        Returns:
            {"success": bool, "data": {"accessToken": "...", "refreshToken": "...", "expiresAt": "..."}}
        """
        if not self.refresh_token:
            return {"success": False, "error": "No refresh token available", "error_code": "NO_REFRESH_TOKEN"}

        response = self._request("POST", f"/{self.VERSION}/account/refresh", data={
            "refreshToken": self.refresh_token
        })

        if response["success"]:
            data = response["data"]
            self.access_token = data["accessToken"]
            self.refresh_token = data["refreshToken"]
            self.token_expiry = data["expiresAt"]
            self._update_headers()
            return {"success": True, "data": data}
        else:
            return response

    # ============== Pool Data Queries ==============

    def get_pools(self) -> Dict[str, Any]:
        """
        Get all trading pools.

        Returns:
            {"success": bool, "data": [{"id": "pool_abc123", "token0": "VEE", "token1": "2100920016", ...}]}
        """
        return self._request("GET", f"/{self.VERSION}/offchain-gex/pools")

    def get_pool_by_item(self, item_id: str) -> Optional[Dict]:
        """
        Get the trading pool for a specific item.

        Args:
            item_id: Item ID (e.g. "2100920016")

        Returns:
            Pool data or None
        """
        response = self.get_pools()
        if response["success"]:
            for pool in response["data"]:
                if pool["token1"] == item_id:
                    return pool
        return None

    def get_item_price(self, item_id: str) -> Optional[float]:
        """
        Calculate the current VEE price of an item.

        Args:
            item_id: Item ID

        Returns:
            VEE price (float) or None
        """
        pool = self.get_pool_by_item(item_id)
        if pool:
            reserve_vee = int(pool["reserve0"]) / 1e18
            reserve_items = int(pool["reserve1"]) / 1e18
            if reserve_items > 0:
                return reserve_vee / reserve_items
        return None

    def get_pool_info(self, item_id: str) -> Dict[str, Any]:
        """
        Get full pool information (reserves, fees, liquidity, etc.).

        Args:
            item_id: Item ID

        Returns:
            {"success": bool, "data": {...}}
        """
        pool = self.get_pool_by_item(item_id)
        if pool:
            reserve_vee = int(pool["reserve0"]) / 1e18
            reserve_items = int(pool["reserve1"]) / 1e18
            price = reserve_vee / reserve_items if reserve_items > 0 else 0
            protocol_fee = float(pool.get("protocolFee", 0))
            lp_fee = float(pool.get("liquidityProviderFee", 0))

            return {
                "success": True,
                "data": {
                    "pool_id": pool["id"],
                    "item_id": item_id,
                    "reserve_vee": reserve_vee,
                    "reserve_items": reserve_items,
                    "price_per_item": price,
                    "protocol_fee_pct": protocol_fee,
                    "lp_fee_pct": lp_fee,
                    "total_fee_pct": protocol_fee + lp_fee,
                    "total_lp_supply": int(pool["totalLpSupply"]) / 1e18,
                }
            }
        return {"success": False, "error": f"Pool not found for item {item_id}"}

    # ============== Price and Trade Data ==============

    def get_recent_trades(self, item_id: str) -> Dict[str, Any]:
        """
        Get recent trades (~250 records).

        Args:
            item_id: Item ID

        Returns:
            {"success": bool, "data": [{"type": "buy"/"sell", "price": "...", "timestamp": "..."}]}
        """
        return self._request("GET", f"/{self.VERSION}/offchain-gex/items/{item_id}/recent_trades")

    def get_candles(self, item_id: str, interval: str = "1h") -> Dict[str, Any]:
        """
        Get candlestick chart data.

        Args:
            item_id: Item ID
            interval: Time interval ("1h" or "1d")

        Returns:
            {"success": bool, "data": [{"timestamp": "...", "open": "...", "high": "...", ...}]}
        """
        return self._request("GET", f"/{self.VERSION}/offchain-gex/items/{item_id}/candles",
                           params={"interval": interval})

    def get_vee_price(self) -> Dict[str, Any]:
        """
        Get VEE USD price across multiple timeframes.

        Returns:
            {"success": bool, "data": {"hour": 0.123, "day": 0.125, ...}}
        """
        return self._request("GET", f"/{self.VERSION}/web3/vee_price")

    # ============== Account Information ==============

    def get_inventory(self) -> Dict[str, Any]:
        """
        Get account item inventory.

        Returns:
            {"success": bool, "data": [{"itemId": "2100920016", "amount": 5, ...}]}
        """
        return self._request("GET", f"/{self.VERSION}/inventory")

    def get_vee_balance(self) -> Dict[str, Any]:
        """
        Get VEE balance.

        Returns:
            {"success": bool, "data": {"earnings": 1000.5}}  (in VEE, not wei)
        """
        return self._request("GET", f"/{self.VERSION}/account/battle")

    def get_liquidity_positions(self) -> Dict[str, Any]:
        """
        Get liquidity provider positions.

        Returns:
            {"success": bool, "data": [{"poolId": "...", "itemId": "...", "lpTokens": "...", ...}]}
        """
        return self._request("GET", f"/{self.VERSION}/offchain-gex/liquidity/positions")

    # ============== Trading ==============

    def swap_vee_for_items(self, item_id: str, item_amount: float, max_vee_amount: float) -> Dict[str, Any]:
        """
        Buy items with VEE.

        Args:
            item_id: Item ID
            item_amount: Purchase quantity (human-readable)
            max_vee_amount: Maximum VEE to spend (slippage protection)

        Returns:
            {"success": bool, "data": {"newVeeReserve": "...", ...}}
        """
        item_amount_wei = int(item_amount * 1e18)
        max_vee_wei = int(max_vee_amount * 1e18)

        return self._request("POST", f"/{self.VERSION}/offchain-gex/swap/vee-for-items", data={
            "itemId": item_id,
            "itemAmount": str(item_amount_wei),
            "maxVeeAmount": str(max_vee_wei)
        })

    def swap_items_for_vee(self, item_id: str, item_amount: float, min_vee_amount: float) -> Dict[str, Any]:
        """
        Sell items for VEE.

        Args:
            item_id: Item ID
            item_amount: Sell quantity (human-readable)
            min_vee_amount: Minimum VEE to receive (slippage protection)

        Returns:
            {"success": bool, "data": {"newVeeReserve": "...", ...}}
        """
        item_amount_wei = int(item_amount * 1e18)
        min_vee_wei = int(min_vee_amount * 1e18)

        return self._request("POST", f"/{self.VERSION}/offchain-gex/swap/items-for-vee", data={
            "itemId": item_id,
            "itemAmount": str(item_amount_wei),
            "minVeeAmount": str(min_vee_wei)
        })

    def calculate_buy_cost(self, item_id: str, item_amount: float) -> Optional[Dict]:
        """
        Calculate the cost to buy items (including fees).

        Args:
            item_id: Item ID
            item_amount: Purchase quantity

        Returns:
            {"vee_cost": float, "fee": float, "total": float} or None
        """
        pool = self.get_pool_by_item(item_id)
        if not pool:
            return None

        reserve_vee = int(pool["reserve0"]) / 1e18
        reserve_items = int(pool["reserve1"]) / 1e18
        fee_pct = float(pool.get("protocolFee", 0.025))
        effective_fee = 1 - fee_pct

        # Formula: vee_cost = (reserve_vee * item_amount) / ((reserve_items - item_amount) * effective_fee)
        if reserve_items <= item_amount:
            return None  # Insufficient liquidity

        vee_cost = (reserve_vee * item_amount) / ((reserve_items - item_amount) * effective_fee)
        fee = vee_cost * fee_pct

        return {
            "item_amount": item_amount,
            "vee_cost": vee_cost,
            "fee": fee,
            "total": vee_cost + fee,
            "fee_pct": fee_pct * 100,
        }

    def calculate_sell_return(self, item_id: str, item_amount: float) -> Optional[Dict]:
        """
        Calculate the return for selling items (after fees).

        Args:
            item_id: Item ID
            item_amount: Sell quantity

        Returns:
            {"vee_received": float, "fee": float, "net": float} or None
        """
        pool = self.get_pool_by_item(item_id)
        if not pool:
            return None

        reserve_vee = int(pool["reserve0"]) / 1e18
        reserve_items = int(pool["reserve1"]) / 1e18
        fee_pct = float(pool.get("protocolFee", 0.025))

        # Formula: vee_received = ((item_amount * (1 - fee_pct)) * reserve_vee) / (reserve_items + item_amount * (1 - fee_pct))
        effective_input = item_amount * (1 - fee_pct)
        vee_received = (effective_input * reserve_vee) / (reserve_items + effective_input)
        fee = item_amount * fee_pct * (reserve_vee / reserve_items)  # approximate fee

        return {
            "item_amount": item_amount,
            "vee_received": vee_received,
            "fee": fee,
            "net": vee_received - fee,
            "fee_pct": fee_pct * 100,
        }

    # ============== Liquidity ==============

    def quote_add_liquidity(self, item_id: str, item_amount: float) -> Dict[str, Any]:
        """
        Preview adding liquidity (does not execute).

        Args:
            item_id: Item ID
            item_amount: Item quantity

        Returns:
            {"success": bool, "data": {"requiredVeeAmount": "...", "lpTokensToReceive": "...", ...}}
        """
        item_amount_wei = int(item_amount * 1e18)

        return self._request("POST", f"/{self.VERSION}/offchain-gex/liquidity/quote/add", data={
            "itemId": item_id,
            "itemAmount": str(item_amount_wei)
        })

    def quote_remove_liquidity(self, item_id: str, lp_tokens: float) -> Dict[str, Any]:
        """
        Preview removing liquidity (does not execute).

        Args:
            item_id: Item ID
            lp_tokens: LP token quantity

        Returns:
            {"success": bool, "data": {"...": "..."}}
        """
        lp_tokens_wei = int(lp_tokens * 1e18)

        return self._request("POST", f"/{self.VERSION}/offchain-gex/liquidity/quote/remove", data={
            "itemId": item_id,
            "lpTokens": str(lp_tokens_wei)
        })

    def add_liquidity(self, item_id: str, item_amount: float, max_vee_amount: float) -> Dict[str, Any]:
        """
        Add liquidity (executes the transaction).

        Args:
            item_id: Item ID
            item_amount: Item quantity
            max_vee_amount: Maximum VEE to pay (slippage protection)

        Returns:
            {"success": bool, "data": {...}}
        """
        item_amount_wei = int(item_amount * 1e18)
        max_vee_wei = int(max_vee_amount * 1e18)

        return self._request("POST", f"/{self.VERSION}/offchain-gex/liquidity/add", data={
            "itemId": item_id,
            "itemAmount": str(item_amount_wei),
            "maxVeeAmount": str(max_vee_wei)
        })

    def remove_liquidity(self, item_id: str, lp_tokens: float) -> Dict[str, Any]:
        """
        Remove liquidity (executes the transaction).

        Args:
            item_id: Item ID
            lp_tokens: LP token quantity

        Returns:
            {"success": bool, "data": {...}}
        """
        lp_tokens_wei = int(lp_tokens * 1e18)

        return self._request("POST", f"/{self.VERSION}/offchain-gex/liquidity/remove", data={
            "itemId": item_id,
            "lpTokens": str(lp_tokens_wei)
        })
