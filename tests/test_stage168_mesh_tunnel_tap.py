r"""
tests/test_stage168_mesh_tunnel_tap.py
Stage 168 Test Suite: Sovereign Mesh Network Tunneling & Virtual TAP/TUN Fabric
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest

from backend.lucy_core.mesh_tunnel_tap import (
    CREATOR,
    DEFAULT_MTU,
    ERA,
    OPERATOR,
    OVERLAY_MTU,
    STAGE,
    STAGE_NAME,
    EthernetFrame,
    InterfaceMode,
    MeshVirtualSwitch,
    OverlayTunnelPacket,
    SovereignMeshTunnelFabric,
    VirtualInterface,
    get_mesh_tunnel_fabric,
)


class TestStage168MeshTunnelTAP(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = SovereignMeshTunnelFabric()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 168)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Sovereign Mesh Network Tunneling & Virtual TAP/TUN Fabric",
        )
        self.assertEqual(DEFAULT_MTU, 1500)
        self.assertEqual(OVERLAY_MTU, 1420)

    def test_02_ethernet_frame_serialization_and_parsing(self) -> None:
        frame = EthernetFrame(
            dst_mac="52:54:00:12:34:56",
            src_mac="52:54:00:65:43:21",
            ethertype=0x0800,
            payload=b"HELLO_IP_PACKET_PAYLOAD",
        )
        serialized = frame.serialize()
        self.assertEqual(len(serialized), 14 + len(b"HELLO_IP_PACKET_PAYLOAD"))

        parsed = EthernetFrame.parse(serialized)
        self.assertEqual(parsed.dst_mac.lower(), "52:54:00:12:34:56")
        self.assertEqual(parsed.src_mac.lower(), "52:54:00:65:43:21")
        self.assertEqual(parsed.ethertype, 0x0800)
        self.assertEqual(parsed.payload, b"HELLO_IP_PACKET_PAYLOAD")

    def test_03_virtual_interface_creation(self) -> None:
        tap = VirtualInterface("tap_test", mode=InterfaceMode.TAP)
        tun = VirtualInterface("tun_test", mode=InterfaceMode.TUN)
        self.assertEqual(tap.mtu, 1500)
        self.assertEqual(tun.mtu, 1420)
        self.assertEqual(tap.tx_packets, 0)
        self.assertEqual(tap.rx_packets, 0)

    def test_04_mtu_enforcement(self) -> None:
        vif = VirtualInterface("tap_limit", mode=InterfaceMode.TAP)
        oversized = b"X" * 1501
        with self.assertRaises(ValueError):
            vif.transmit(oversized)

    def test_05_cam_mac_learning(self) -> None:
        switch = MeshVirtualSwitch()
        v1 = VirtualInterface("eth0", mac="52:54:00:00:00:01")
        switch.attach_interface(v1)
        self.assertIn("52:54:00:00:00:01", switch.cam_table)
        self.assertEqual(switch.cam_table["52:54:00:00:00:01"][0], "eth0")

    def test_06_unicast_frame_switching(self) -> None:
        switch = MeshVirtualSwitch()
        v1 = VirtualInterface("eth0", mac="52:54:00:00:00:01")
        v2 = VirtualInterface("eth1", mac="52:54:00:00:00:02")
        switch.attach_interface(v1)
        switch.attach_interface(v2)

        frame = EthernetFrame(
            dst_mac="52:54:00:00:00:02",
            src_mac="52:54:00:00:00:01",
            ethertype=0x0800,
            payload=b"UNICAST_PAYLOAD",
        )
        routed = switch.route_frame(frame, incoming_if="eth0")
        self.assertEqual(routed, ["eth1"])
        self.assertEqual(len(v2.rx_queue), 1)
        self.assertEqual(len(v1.rx_queue), 0)

    def test_07_broadcast_frame_flooding(self) -> None:
        switch = MeshVirtualSwitch()
        v1 = VirtualInterface("eth0", mac="52:54:00:00:00:01")
        v2 = VirtualInterface("eth1", mac="52:54:00:00:00:02")
        v3 = VirtualInterface("eth2", mac="52:54:00:00:00:03")
        switch.attach_interface(v1)
        switch.attach_interface(v2)
        switch.attach_interface(v3)

        bcast_frame = EthernetFrame(
            dst_mac="FF:FF:FF:FF:FF:FF",
            src_mac="52:54:00:00:00:01",
            ethertype=0x0806,  # ARP
            payload=b"ARP_WHO_HAS_IP",
        )
        routed = switch.route_frame(bcast_frame, incoming_if="eth0")
        self.assertIn("eth1", routed)
        self.assertIn("eth2", routed)
        self.assertNotIn("eth0", routed)

    def test_08_overlay_packet_signature_and_verification(self) -> None:
        pkt = self.fabric.create_encrypted_overlay(
            seq_num=101,
            sender_key="pubkey_senin",
            recipient_key="pubkey_peer",
            payload=b"ENCRYPTED_WIREGUARD_PAYLOAD",
        )
        self.assertTrue(pkt.verify())
        self.assertEqual(len(pkt.hmac_digest), 64)

        # Tampered packet fails verification
        pkt.encrypted_payload = b"TAMPERED_WIREGUARD_PAYLOAD"
        self.assertFalse(pkt.verify())

    def test_09_fabric_send_ethernet_integration(self) -> None:
        ok, targets = self.fabric.send_ethernet_packet(
            src_if="tap0",
            dst_mac="52:54:00:aa:bb:02",
            payload=b"TCP_SYN_PACKET",
        )
        self.assertTrue(ok)
        self.assertIn("tap1", targets)
        self.assertEqual(self.fabric.total_tunneled_packets, 1)

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("LUCY STAGE 168: SOVEREIGN MESH TUNNELING", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Virtual Switch", ascii_out)
        self.assertIn("Crypto-Routes", ascii_out)

        f1 = get_mesh_tunnel_fabric()
        f2 = get_mesh_tunnel_fabric()
        self.assertIs(f1, f2)


if __name__ == "__main__":
    unittest.main()
