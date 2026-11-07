"""
tests/test_stage245_orbital_constellation_grid.py
Unit tests for Stage 245: Hyper-Scale Neuromorphic Astro-Grid Orbital Constellation Coordinator
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.getcwd())

from backend.lucy_core.orbital_constellation_grid import (
    STAGE,
    STAGE_NAME,
    ERA,
    RADIUS_EARTH_KM,
    KeplerianElements,
    OrbitalConstellationGridFabric
)


class TestStage245OrbitalConstellationGrid(unittest.TestCase):

    def test_01_keplerian_elements_period(self):
        """Test Keplerian orbital period formula T = 2*pi*sqrt(a^3 / mu)."""
        # LEO orbit at 550 km: a = 6378.137 + 550 = 6928.137 km
        elems = KeplerianElements(
            semi_major_axis_km=6928.137,
            eccentricity=0.001,
            inclination_deg=53.0,
            raan_deg=0.0,
            arg_periapsis_deg=0.0,
            true_anomaly_deg=0.0
        )
        period_s = elems.orbital_period_seconds
        period_min = period_s / 60.0
        # ~95.6 minutes
        self.assertAlmostEqual(period_min, 95.6, places=1)

    def test_02_walker_delta_constellation_dimensions(self):
        """Test Walker Delta initialization creates 4 planes * 12 sats = 48 satellites."""
        fabric = OrbitalConstellationGridFabric(num_planes=4, sats_per_plane=12, altitude_km=550.0)
        self.assertEqual(len(fabric.satellites), 48)
        self.assertIn("sat_p00_s00", fabric.satellites)
        self.assertIn("sat_p03_s11", fabric.satellites)

    def test_03_position_propagation_circular_radius(self):
        """Test propagated ECI position maintains correct radial distance."""
        fabric = OrbitalConstellationGridFabric(altitude_km=550.0)
        sat = fabric.satellites["sat_p00_s00"]
        pos = sat.get_position_km(epoch_seconds=100.0)
        r = math.sqrt(pos[0] ** 2 + pos[1] ** 2 + pos[2] ** 2)
        expected_r = RADIUS_EARTH_KM + 550.0
        self.assertAlmostEqual(r, expected_r, places=1)

    def test_04_adjacent_in_plane_isl_line_of_sight(self):
        """Test adjacent satellites in the same plane have clear optical line of sight."""
        fabric = OrbitalConstellationGridFabric(num_planes=4, sats_per_plane=12)
        res = fabric.check_inter_satellite_link("sat_p00_s00", "sat_p00_s01", epoch_seconds=0.0)
        self.assertTrue(res["line_of_sight_clear"])
        self.assertEqual(res["status"], "LINK_ESTABLISHED")
        self.assertGreater(res["distance_km"], 1000.0)
        self.assertLess(res["distance_km"], 8000.0)

    def test_05_optical_latency_calculation(self):
        """Test optical latency tau = distance / c in milliseconds."""
        fabric = OrbitalConstellationGridFabric()
        res = fabric.check_inter_satellite_link("sat_p00_s00", "sat_p00_s01")
        dist = res["distance_km"]
        expected_lat = (dist / 299792.458) * 1000.0
        self.assertAlmostEqual(res["optical_latency_ms"], expected_lat, places=2)

    def test_06_antipodal_satellite_earth_occultation(self):
        """Test satellites on opposite sides of Earth are blocked by Earth occultation."""
        fabric = OrbitalConstellationGridFabric(num_planes=4, sats_per_plane=12)
        # s00 and s06 are separated by 180 degrees in the same plane
        res = fabric.check_inter_satellite_link("sat_p00_s00", "sat_p00_s06", epoch_seconds=0.0)
        self.assertFalse(res["line_of_sight_clear"])
        self.assertEqual(res["status"], "EARTH_OCCULTED")
        self.assertLess(res["closest_approach_km"], RADIUS_EARTH_KM)

    def test_07_dtn_direct_bundle_delivery(self):
        """Test direct delivery of bundle when line of sight is clear."""
        fabric = OrbitalConstellationGridFabric()
        payload = {"telemetry": "QUANTUM_ORBITAL_TELEMETRY", "timestamp": 12345}
        res = fabric.route_dtn_bundle("sat_p00_s00", "sat_p00_s01", payload)

        self.assertEqual(res["status"], "DELIVERED_DIRECT")
        self.assertEqual(res["hops"], 1)
        self.assertIn(payload, fabric.satellites["sat_p00_s01"].custody_bundles)

    def test_08_dtn_relay_bundle_delivery(self):
        """Test custody relay when direct link is occulted."""
        fabric = OrbitalConstellationGridFabric()
        payload = {"mission": "ASTRO_COGNITIVE_CORES"}
        res = fabric.route_dtn_bundle("sat_p00_s00", "sat_p00_s06", payload)

        self.assertIn(res["status"], {"CUSTODY_RELAYED", "STORED_IN_CUSTODY_DTN_WAITING_WINDOW"})
        self.assertGreaterEqual(fabric.total_routed_bundles, 1)

    def test_09_fabric_status_dictionary(self):
        """Test status dictionary output."""
        fabric = OrbitalConstellationGridFabric(num_planes=4, sats_per_plane=12)
        st = fabric.status()
        self.assertEqual(st["stage"], 245)
        self.assertEqual(st["era"], 25)
        self.assertEqual(st["total_satellites"], 48)
        self.assertEqual(st["orbital_planes"], 4)
        self.assertIn("orbital_period_minutes", st)

    def test_10_ascii_status_table(self):
        """Test CP1252-safe ASCII table formatting."""
        fabric = OrbitalConstellationGridFabric()
        tbl = fabric.format_ascii_status()
        self.assertIn("STAGE 245", tbl)
        self.assertIn("Constellation Grid", tbl)
        self.assertIn("Orbit Altitude", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
