"""
Integration tests for ZeeVerseGEX client.
Uses real API calls with provided credentials.

Run from the skill root:
    cd skills/zeeverse-gex-trading
    python -m pytest scripts/tests/ -v
"""

import sys
import os
import pytest

# Add scripts directory to path so gex_client can be imported directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gex_client import ZeeVerseGEX

# ============================================================
# Test credentials and constants
# ============================================================
TEST_EMAIL = "599108838@qq.com"
TEST_PASSWORD = "Genouswhy830924!"
TEST_ITEM_ID = "2100920016"  # Snorker — most liquid pool, safe for testing


# ============================================================
# Shared fixture: authenticated client (login once per session)
# ============================================================
@pytest.fixture(scope="module")
def client():
    """Create an authenticated ZeeVerseGEX client."""
    c = ZeeVerseGEX()
    result = c.login(TEST_EMAIL, TEST_PASSWORD)
    assert result["success"], f"Login failed: {result.get('error')}"
    assert c.access_token, "access_token not set after login"
    return c


# ============================================================
# Authentication tests
# ============================================================
class TestAuthentication:
    def test_login_success(self):
        """Login with valid credentials returns tokens."""
        c = ZeeVerseGEX()
        result = c.login(TEST_EMAIL, TEST_PASSWORD)
        assert result["success"] is True
        assert "accessToken" in result["data"]
        assert "refreshToken" in result["data"]
        assert c.access_token is not None

    def test_login_failure_wrong_password(self):
        """Login with wrong password returns error, not exception."""
        c = ZeeVerseGEX()
        result = c.login(TEST_EMAIL, "wrongpassword_xyz")
        assert result["success"] is False
        assert "error" in result

    def test_refresh_token(self, client):
        """Token refresh returns new tokens."""
        result = client.refresh()
        assert result["success"] is True
        assert "accessToken" in result["data"]

    def test_refresh_no_token(self):
        """Refresh without refresh_token returns NO_REFRESH_TOKEN error."""
        c = ZeeVerseGEX()
        result = c.refresh()
        assert result["success"] is False
        assert result["error_code"] == "NO_REFRESH_TOKEN"


# ============================================================
# Pool query tests
# ============================================================
class TestPoolQueries:
    def test_get_pools_returns_list(self, client):
        """get_pools returns a non-empty list of pool objects."""
        result = client.get_pools()
        assert result["success"] is True
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_pools_pool_structure(self, client):
        """Each pool has required fields."""
        result = client.get_pools()
        assert result["success"] is True
        pool = result["data"][0]
        for field in ("id", "reserve0", "reserve1", "token0", "token1"):
            assert field in pool, f"Pool missing field: {field}"

    def test_get_pool_by_item_found(self, client):
        """get_pool_by_item finds Snorker pool."""
        pool = client.get_pool_by_item(TEST_ITEM_ID)
        assert pool is not None
        assert pool["token1"] == TEST_ITEM_ID

    def test_get_pool_by_item_not_found(self, client):
        """get_pool_by_item returns None for non-existent item."""
        pool = client.get_pool_by_item("9999999999")
        assert pool is None

    def test_get_item_price_positive(self, client):
        """get_item_price returns a positive float."""
        price = client.get_item_price(TEST_ITEM_ID)
        assert price is not None
        assert isinstance(price, float)
        assert price > 0

    def test_get_item_price_nonexistent(self, client):
        """get_item_price returns None for unknown item."""
        price = client.get_item_price("9999999999")
        assert price is None

    def test_get_pool_info_structure(self, client):
        """get_pool_info returns all expected fields."""
        result = client.get_pool_info(TEST_ITEM_ID)
        assert result["success"] is True
        data = result["data"]
        for field in ("pool_id", "item_id", "reserve_vee", "reserve_items",
                      "price_per_item", "protocol_fee_pct", "lp_fee_pct",
                      "total_fee_pct", "total_lp_supply"):
            assert field in data, f"pool_info missing field: {field}"

    def test_get_pool_info_values_positive(self, client):
        """Pool reserves and price are all positive."""
        result = client.get_pool_info(TEST_ITEM_ID)
        assert result["success"] is True
        data = result["data"]
        assert data["reserve_vee"] > 0
        assert data["reserve_items"] > 0
        assert data["price_per_item"] > 0

    def test_get_pool_info_not_found(self, client):
        """get_pool_info returns error for unknown item."""
        result = client.get_pool_info("9999999999")
        assert result["success"] is False
        assert "error" in result


# ============================================================
# Price and trade data tests
# ============================================================
class TestPriceData:
    def test_get_recent_trades(self, client):
        """get_recent_trades returns a list."""
        result = client.get_recent_trades(TEST_ITEM_ID)
        assert result["success"] is True
        assert isinstance(result["data"], list)

    def test_get_candles_1h(self, client):
        """get_candles with 1h interval returns data."""
        result = client.get_candles(TEST_ITEM_ID, interval="1h")
        assert result["success"] is True
        assert isinstance(result["data"], list)

    def test_get_candles_1d(self, client):
        """get_candles with 1d interval returns data."""
        result = client.get_candles(TEST_ITEM_ID, interval="1d")
        assert result["success"] is True

    def test_get_vee_price(self, client):
        """get_vee_price returns success."""
        result = client.get_vee_price()
        assert result["success"] is True
        assert isinstance(result["data"], dict)


# ============================================================
# Account information tests
# ============================================================
class TestAccountInfo:
    def test_get_inventory(self, client):
        """get_inventory succeeds (may be empty list)."""
        result = client.get_inventory()
        assert result["success"] is True
        assert isinstance(result["data"], list)

    def test_get_vee_balance(self, client):
        """get_vee_balance returns success."""
        result = client.get_vee_balance()
        assert result["success"] is True

    def test_get_liquidity_positions(self, client):
        """get_liquidity_positions returns success."""
        result = client.get_liquidity_positions()
        assert result["success"] is True


# ============================================================
# Cost calculation tests (local math on real pool data)
# ============================================================
class TestCostCalculation:
    def test_calculate_buy_cost_keys(self, client):
        """calculate_buy_cost returns dict with expected keys."""
        result = client.calculate_buy_cost(TEST_ITEM_ID, 1.0)
        assert result is not None
        for key in ("item_amount", "vee_cost", "fee", "total", "fee_pct"):
            assert key in result, f"Missing key: {key}"

    def test_calculate_buy_cost_values_positive(self, client):
        """Buy cost components are all positive."""
        result = client.calculate_buy_cost(TEST_ITEM_ID, 1.0)
        assert result is not None
        assert result["vee_cost"] > 0
        assert result["fee"] > 0
        assert result["total"] > result["vee_cost"]  # total includes fee

    def test_calculate_buy_cost_item_amount_preserved(self, client):
        """item_amount field matches what was passed in."""
        result = client.calculate_buy_cost(TEST_ITEM_ID, 3.0)
        assert result is not None
        assert result["item_amount"] == 3.0

    def test_calculate_buy_cost_insufficient_liquidity(self, client):
        """Buying more than pool reserve returns None."""
        result = client.calculate_buy_cost(TEST_ITEM_ID, 999_999_999.0)
        assert result is None

    def test_calculate_buy_cost_unknown_item(self, client):
        """Unknown item returns None."""
        result = client.calculate_buy_cost("9999999999", 1.0)
        assert result is None

    def test_calculate_sell_return_keys(self, client):
        """calculate_sell_return returns dict with expected keys."""
        result = client.calculate_sell_return(TEST_ITEM_ID, 1.0)
        assert result is not None
        for key in ("item_amount", "vee_received", "fee", "net", "fee_pct"):
            assert key in result, f"Missing key: {key}"

    def test_calculate_sell_return_values_positive(self, client):
        """Sell return components are positive."""
        result = client.calculate_sell_return(TEST_ITEM_ID, 1.0)
        assert result is not None
        assert result["vee_received"] > 0
        assert result["fee"] >= 0

    def test_calculate_sell_return_unknown_item(self, client):
        """Unknown item returns None."""
        result = client.calculate_sell_return("9999999999", 1.0)
        assert result is None

    def test_buy_more_expensive_than_sell(self, client):
        """Buying 1 unit costs more VEE than selling 1 unit returns."""
        buy = client.calculate_buy_cost(TEST_ITEM_ID, 1.0)
        sell = client.calculate_sell_return(TEST_ITEM_ID, 1.0)
        assert buy is not None and sell is not None
        # Buy total > sell net (bid-ask spread from AMM fees)
        assert buy["total"] > sell["net"]


# ============================================================
# Trade execution tests (expect API-level errors, not crashes)
# ============================================================
class TestTradeExecution:
    def test_swap_vee_for_items_low_max_vee_fails_gracefully(self, client):
        """
        Buying with max_vee=0.001 (way too low) should fail with a known
        error code — not raise an exception.
        """
        result = client.swap_vee_for_items(TEST_ITEM_ID, 1.0, 0.001)
        assert result["success"] is False
        assert "error" in result
        # Should be slippage, insufficient balance, or similar — not a crash
        assert result.get("error_code") is not None or result.get("error") is not None

    def test_swap_items_for_vee_high_min_vee_fails_gracefully(self, client):
        """
        Selling with min_vee=9999 (unreachably high) should fail with a known
        error code — not raise an exception.
        """
        result = client.swap_items_for_vee(TEST_ITEM_ID, 1.0, 9999.0)
        assert result["success"] is False
        assert "error" in result
        assert result.get("error_code") is not None or result.get("error") is not None


# ============================================================
# Liquidity quote tests (read-only previews)
# ============================================================
class TestLiquidityQuotes:
    def test_quote_add_liquidity(self, client):
        """quote_add_liquidity returns a response (success or known error)."""
        result = client.quote_add_liquidity(TEST_ITEM_ID, 1.0)
        # May succeed or fail depending on pool state — must not crash
        assert "success" in result

    def test_quote_add_liquidity_structure_on_success(self, client):
        """If quote_add_liquidity succeeds, data is a dict."""
        result = client.quote_add_liquidity(TEST_ITEM_ID, 1.0)
        if result["success"]:
            assert isinstance(result["data"], dict)

    def test_quote_remove_liquidity(self, client):
        """quote_remove_liquidity returns a response (may fail if no LP)."""
        result = client.quote_remove_liquidity(TEST_ITEM_ID, 0.01)
        # Will fail if account has no LP tokens — but must not crash
        assert "success" in result
