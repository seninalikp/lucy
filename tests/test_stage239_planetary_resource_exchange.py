"""
tests/test_stage239_planetary_resource_exchange.py
Unit tests for Stage 239: Planetary Sovereign Autonomous Resource Exchange & Zero-Sum Tokenless Ledger
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity
"""

import unittest
from backend.lucy_core.planetary_resource_exchange import (
    STAGE,
    STAGE_NAME,
    ERA,
    CommodityType,
    OrderSide,
    PlanetaryResourceExchangeFabric
)


class TestStage239PlanetaryResourceExchange(unittest.TestCase):

    def test_01_sovereign_nodes_and_zero_initial_balances(self):
        """Test default node registration and initial zero balances."""
        exchange = PlanetaryResourceExchangeFabric()
        self.assertGreaterEqual(len(exchange.nodes), 4)
        for nid, bal in exchange.balances.items():
            self.assertEqual(bal, 0.0)

        is_zero, leak = exchange.verify_zero_sum_invariant()
        self.assertTrue(is_zero)
        self.assertEqual(leak, 0.0)

    def test_02_limit_order_placement_and_sorting(self):
        """Test limit orders sort properly: bids desc, asks asc."""
        exchange = PlanetaryResourceExchangeFabric()
        comm = CommodityType.COMPUTE_PETAFLOPS

        exchange.place_limit_order("node_sol_prime", comm, OrderSide.BID, quantity=5.0, price=80.0)
        exchange.place_limit_order("node_luna_gateway", comm, OrderSide.BID, quantity=5.0, price=95.0)

        exchange.place_limit_order("node_mars_deep_core", comm, OrderSide.ASK, quantity=5.0, price=120.0)
        exchange.place_limit_order("node_orbital_photonic", comm, OrderSide.ASK, quantity=5.0, price=110.0)

        ob = exchange.order_books[comm]
        self.assertEqual(ob["bids"][0].price, 95.0)
        self.assertEqual(ob["bids"][1].price, 80.0)
        self.assertEqual(ob["asks"][0].price, 110.0)
        self.assertEqual(ob["asks"][1].price, 120.0)

    def test_03_continuous_double_auction_execution(self):
        """Test continuous double auction matching and midpoint price clearing."""
        exchange = PlanetaryResourceExchangeFabric()
        comm = CommodityType.COMPUTE_PETAFLOPS

        # Place ask first: 10 units at 100.0
        exchange.place_limit_order("node_sol_prime", comm, OrderSide.ASK, quantity=10.0, price=100.0)
        # Place bid crossing spread: 10 units at 120.0
        exchange.place_limit_order("node_luna_gateway", comm, OrderSide.BID, quantity=10.0, price=120.0)

        self.assertEqual(len(exchange.trade_history), 1)
        trade = exchange.trade_history[0]
        self.assertEqual(trade.commodity, comm)
        self.assertEqual(trade.buyer_node, "node_luna_gateway")
        self.assertEqual(trade.seller_node, "node_sol_prime")
        self.assertEqual(trade.clearing_price, 110.0) # (100 + 120) / 2
        self.assertEqual(trade.quantity, 10.0)
        self.assertEqual(trade.total_value, 1100.0)

        # Buyer balance -= 1100, Seller balance += 1100
        self.assertEqual(exchange.balances["node_luna_gateway"], -1100.0)
        self.assertEqual(exchange.balances["node_sol_prime"], 1100.0)

    def test_04_zero_sum_conservation_post_trade(self):
        """Test strict zero-sum conservation invariant holds after transactions."""
        exchange = PlanetaryResourceExchangeFabric()
        comm = CommodityType.PHOTONIC_MZI_CYCLES

        exchange.place_limit_order("node_mars_deep_core", comm, OrderSide.ASK, quantity=50.0, price=2.0)
        exchange.place_limit_order("node_orbital_photonic", comm, OrderSide.BID, quantity=50.0, price=4.0)

        is_zero, leak = exchange.verify_zero_sum_invariant()
        self.assertTrue(is_zero)
        self.assertEqual(leak, 0.0)
        self.assertEqual(sum(exchange.balances.values()), 0.0)

    def test_05_multi_commodity_isolated_order_books(self):
        """Test order books for different commodities do not cross."""
        exchange = PlanetaryResourceExchangeFabric()
        exchange.place_limit_order("node_sol_prime", CommodityType.COMPUTE_PETAFLOPS, OrderSide.BID, 10.0, 100.0)
        exchange.place_limit_order("node_luna_gateway", CommodityType.MEMORY_TERABYTES, OrderSide.ASK, 10.0, 90.0)

        # No trade should occur because commodities differ
        self.assertEqual(len(exchange.trade_history), 0)

    def test_06_partial_order_fills(self):
        """Test partial filling leaves remaining quantity in order book."""
        exchange = PlanetaryResourceExchangeFabric()
        comm = CommodityType.BANDWIDTH_TERABITS

        exchange.place_limit_order("node_sol_prime", comm, OrderSide.ASK, quantity=10.0, price=50.0)
        exchange.place_limit_order("node_mars_deep_core", comm, OrderSide.BID, quantity=4.0, price=60.0)

        self.assertEqual(len(exchange.trade_history), 1)
        trade = exchange.trade_history[0]
        self.assertEqual(trade.quantity, 4.0)

        ob = exchange.order_books[comm]
        self.assertEqual(len(ob["bids"]), 0) # Bid fully filled
        self.assertEqual(len(ob["asks"]), 1) # Ask partially remaining
        self.assertEqual(ob["asks"][0].remaining, 6.0)

    def test_07_prevent_self_trading(self):
        """Test self-trading prevention when node bids and asks on same commodity."""
        exchange = PlanetaryResourceExchangeFabric()
        comm = CommodityType.QUANTUM_GATE_CYCLES

        exchange.place_limit_order("node_sol_prime", comm, OrderSide.ASK, quantity=10.0, price=500.0)
        exchange.place_limit_order("node_sol_prime", comm, OrderSide.BID, quantity=10.0, price=600.0)

        self.assertEqual(len(exchange.trade_history), 0)

    def test_08_market_spread_calculation(self):
        """Test market spread computation."""
        exchange = PlanetaryResourceExchangeFabric()
        comm = CommodityType.COMPUTE_PETAFLOPS

        exchange.place_limit_order("node_sol_prime", comm, OrderSide.BID, 5.0, 90.0)
        exchange.place_limit_order("node_luna_gateway", comm, OrderSide.ASK, 5.0, 110.0)

        spread_info = exchange.get_market_spread(comm)
        self.assertEqual(spread_info["best_bid"], 90.0)
        self.assertEqual(spread_info["best_ask"], 110.0)
        self.assertEqual(spread_info["spread"], 20.0)

    def test_09_multilateral_debt_cancellation(self):
        """Test multi-lateral debt cancellation algorithm."""
        exchange = PlanetaryResourceExchangeFabric()
        # Simulate non-zero balances
        exchange.balances["node_sol_prime"] = 500.0
        exchange.balances["node_luna_gateway"] = -500.0

        cancelled = exchange.cancel_debt_cycles()
        self.assertGreaterEqual(cancelled, 1)

    def test_10_fabric_status_and_ascii_table(self):
        """Test status dictionary and CP1252-safe ASCII table."""
        exchange = PlanetaryResourceExchangeFabric()
        st = exchange.status()
        self.assertEqual(st["stage"], 239)
        self.assertEqual(st["era"], 24)
        self.assertTrue(st["zero_sum_conserved"])

        tbl = exchange.format_ascii_status()
        self.assertIn("STAGE 239", tbl)
        self.assertIn("Sovereign Nodes", tbl)
        self.assertIn("Zero-Sum Invariant", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
