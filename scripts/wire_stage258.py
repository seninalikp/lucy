"""
scripts/wire_stage258.py
Wires Stage 258 RelativisticChronoSynchronizerFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.josephson_squid_magnetometer import JosephsonSquidMagnetometerFabric, STAGE as STAGE_257\n'
    replacement_import = target_import + 'from backend.lucy_core.relativistic_chrono_synchronizer import RelativisticChronoSynchronizerFabric, STAGE as STAGE_258\n'
    if 'relativistic_chrono_synchronizer' not in text:
        assert target_import in text, 'Target import for Stage 257 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 257: Superconducting Josephson SQUID Magnetometer (Era 26)\n        self.squid_magnetometer = JosephsonSquidMagnetometerFabric()\n'
    replacement_init = target_init + '        # Stage 258: Relativistic Astro-Chronometric Synchronizer (Era 26)\n        self.chrono_synchronizer = RelativisticChronoSynchronizerFabric()\n'
    if 'self.chrono_synchronizer' not in text:
        assert target_init in text, 'Target init for Stage 257 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("squid_magnetometer", "core"),\n'
    replacement_service = target_service + '            ("chrono_synchronizer", "core"),\n'
    if '("chrono_synchronizer", "core")' not in text:
        assert target_service in text, 'Target service for Stage 257 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 258 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /josephson-frequency <voltage_volts>")\n'
    assert target in text, 'Target end of Stage 257 block not found'

    insertion = """
        # Stage 258: Planetary Astro-Chronometric Relativistic Gravitational Time-Dilation Synchronizer
        if lowered in {"/relativistic-chrono-status", "relativistic-chrono-status", "/chrono-sync-status", "chrono-sync-status"}:
            if hasattr(self.runtime, "chrono_synchronizer"):
                tbl = self.runtime.chrono_synchronizer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.chrono_synchronizer.get_metrics())
            return RouterResponse("Chrono synchronizer not available.")

        if lowered.startswith("/orbit-dilation ") or lowered.startswith("orbit-dilation "):
            if hasattr(self.runtime, "chrono_synchronizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    alt_km = float(parts[1])
                    body = parts[2] if len(parts) >= 3 else "earth"
                    offset = self.runtime.chrono_synchronizer.compute_orbit_dilation(alt_km * 1000.0, body)
                    msg = (
                        f"Orbital Relativistic Dilation ({offset.body}, alt={alt_km} km): "
                        f"Net Drift={offset.drift_microseconds_per_day:+.2f} us/day "
                        f"(Grav={offset.gravitational_shift_ratio*86400*1e6:+.2f} us/day, "
                        f"Kin={offset.kinematic_shift_ratio*86400*1e6:.2f} us/day)."
                    )
                    return RouterResponse(msg, data={
                        "body": offset.body,
                        "altitude_km": alt_km,
                        "net_drift_us_per_day": offset.drift_microseconds_per_day,
                        "grav_us": offset.gravitational_shift_ratio * 86400 * 1e6,
                        "kin_us": offset.kinematic_shift_ratio * 86400 * 1e6,
                    })
            return RouterResponse("Usage: /orbit-dilation <altitude_km> [body]")

        if lowered.startswith("/clock-sync ") or lowered.startswith("clock-sync "):
            if hasattr(self.runtime, "chrono_synchronizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    raw_sec = float(parts[1])
                    alt_km = float(parts[2])
                    days = float(parts[3])
                    body = parts[4] if len(parts) >= 5 else "earth"
                    res = self.runtime.chrono_synchronizer.synchronize_clock(raw_sec, alt_km * 1000.0, days, body)
                    msg = (
                        f"Synchronized Clock ({res['body']}, {days} days): "
                        f"Raw={res['raw_clock_sec']:.6f}s -> Corrected={res['corrected_time_sec']:.6f}s "
                        f"(Drift Offset={res['accumulated_drift_us']:+.2f} us)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /clock-sync <raw_clock_sec> <altitude_km> <elapsed_days> [body]")
"""
    if 'relativistic-chrono-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 258 into router.py')
    else:
        print('Stage 258 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
