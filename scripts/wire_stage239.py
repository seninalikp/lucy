"""
scripts/wire_stage239.py
Wires Stage 239 PlanetaryResourceExchangeFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.byzantine_swarm_consensus import ByzantineSwarmConsensusFabric, STAGE as STAGE_238\n'
    replacement_import = target_import + 'from backend.lucy_core.planetary_resource_exchange import PlanetaryResourceExchangeFabric, STAGE as STAGE_239\n'
    if 'planetary_resource_exchange' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 238: Self-Healing Chaos Immunity & Byzantine Swarm Consensus Auto-Recovery (Era 24)\n        self.byzantine_swarm_consensus = ByzantineSwarmConsensusFabric()\n'
    replacement_init = target_init + '        # Stage 239: Planetary Sovereign Autonomous Resource Exchange & Zero-Sum Tokenless Ledger (Era 24)\n        self.planetary_resource_exchange = PlanetaryResourceExchangeFabric()\n'
    if 'self.planetary_resource_exchange' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("byzantine_swarm_consensus", "core"),\n'
    replacement_service = target_service + '            ("planetary_resource_exchange", "core"),\n'
    if '("planetary_resource_exchange", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 239 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /byzantine-recover <node_id>")\n'
    assert target in text, 'Target end of Stage 238 block not found'

    insertion = """
        # Stage 239: Planetary Sovereign Autonomous Resource Exchange & Zero-Sum Tokenless Ledger
        if lowered in {"/resource-exchange-status", "resource-exchange-status"}:
            if hasattr(self.runtime, "planetary_resource_exchange"):
                tbl = self.runtime.planetary_resource_exchange.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.planetary_resource_exchange.status())
            return RouterResponse("Planetary resource exchange fabric not available.")

        if lowered.startswith("/resource-order ") or lowered.startswith("resource-order "):
            if hasattr(self.runtime, "planetary_resource_exchange"):
                parts = raw_text.strip().split()
                if len(parts) >= 6:
                    from backend.lucy_core.planetary_resource_exchange import CommodityType, OrderSide
                    nid, comm_str, side_str, q_str, p_str = parts[1], parts[2].upper(), parts[3].upper(), parts[4], parts[5]
                    try:
                        comm = CommodityType[comm_str]
                        side = OrderSide[side_str]
                        qty = float(q_str)
                        price = float(p_str)
                        order = self.runtime.planetary_resource_exchange.place_limit_order(nid, comm, side, qty, price)
                        msg = f"Limit order '{order.order_id}' placed for node '{nid}': {side.value} {qty} {comm.value} @ {price}."
                        return RouterResponse(msg, data={"order_id": order.order_id, "filled": order.filled, "remaining": order.remaining})
                    except Exception as e:
                        return RouterResponse(f"Resource order placement failed: {e}")
            return RouterResponse("Usage: /resource-order <node_id> <commodity> <BID|ASK> <qty> <price>")

        if lowered.startswith("/resource-spread ") or lowered.startswith("resource-spread "):
            if hasattr(self.runtime, "planetary_resource_exchange"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    from backend.lucy_core.planetary_resource_exchange import CommodityType
                    comm_str = parts[1].upper()
                    try:
                        comm = CommodityType[comm_str]
                        sp = self.runtime.planetary_resource_exchange.get_market_spread(comm)
                        msg = f"Market spread for {comm.value}: Best Bid={sp['best_bid']}, Best Ask={sp['best_ask']}, Spread={sp['spread']}."
                        return RouterResponse(msg, data=sp)
                    except Exception as e:
                        return RouterResponse(f"Market spread query failed: {e}")
            return RouterResponse("Usage: /resource-spread <commodity>")

        if lowered.startswith("/resource-balance ") or lowered.startswith("resource-balance "):
            if hasattr(self.runtime, "planetary_resource_exchange"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nid = parts[1]
                    bal = self.runtime.planetary_resource_exchange.balances.get(nid, 0.0)
                    msg = f"Node '{nid}' net mutual credit balance: {bal:.2f} Units."
                    return RouterResponse(msg, data={"node": nid, "balance": bal})
            return RouterResponse("Usage: /resource-balance <node_id>")
"""
    if 'resource-exchange-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 239 into router.py')
    else:
        print('Stage 239 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
