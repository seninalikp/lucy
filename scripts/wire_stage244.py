"""
scripts/wire_stage244.py
Wires Stage 244 DnaMolecularStorageFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.cellular_cohomology_sheaf import CellularCohomologySheafFabric, STAGE as STAGE_243\n'
    replacement_import = target_import + 'from backend.lucy_core.dna_molecular_storage import DnaMolecularStorageFabric, STAGE as STAGE_244\n'
    if 'dna_molecular_storage' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 243: Deep Sheaf-Theoretic Distributed Multi-Sensor Consistency & Cellular Cohomology Engine (Era 25)\n        self.cellular_cohomology_sheaf = CellularCohomologySheafFabric()\n'
    replacement_init = target_init + '        # Stage 244: Autonomous Synthetic Biology DNA/RNA Storage Codec & Transceiver (Era 25)\n        self.dna_molecular_storage = DnaMolecularStorageFabric()\n'
    if 'self.dna_molecular_storage' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("cellular_cohomology_sheaf", "core"),\n'
    replacement_service = target_service + '            ("dna_molecular_storage", "core"),\n'
    if '("dna_molecular_storage", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 244 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /sheaf-set-sensor <vertex_id> <values_csv>")\n'
    assert target in text, 'Target end of Stage 243 block not found'

    insertion = """
        # Stage 244: Autonomous Synthetic Biology DNA/RNA Storage Codec & Error-Correcting Transceiver
        if lowered in {"/dna-storage-status", "dna-storage-status"}:
            if hasattr(self.runtime, "dna_molecular_storage"):
                tbl = self.runtime.dna_molecular_storage.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.dna_molecular_storage.status())
            return RouterResponse("DNA molecular storage fabric not available.")

        if lowered.startswith("/dna-encode ") or lowered.startswith("dna-encode "):
            if hasattr(self.runtime, "dna_molecular_storage"):
                parts = raw_text.strip().split(maxsplit=1)
                if len(parts) >= 2:
                    raw_data = parts[1].encode("utf-8")
                    strands = self.runtime.dna_molecular_storage.encode_data_to_oligo_pool(raw_data)
                    first_seq = strands[0].full_sequence[:32] if strands else ""
                    msg = (
                        f"Encoded {len(raw_data)} bytes into {len(strands)} DNA oligo strands. "
                        f"Leading Oligo: {first_seq}... (GC: {strands[0].gc_content * 100:.1f}%)."
                    )
                    return RouterResponse(msg, data={"bytes_encoded": len(raw_data), "strands_count": len(strands)})
            return RouterResponse("Usage: /dna-encode <utf8_text_or_data>")

        if lowered in {"/dna-decode", "dna-decode"}:
            if hasattr(self.runtime, "dna_molecular_storage"):
                try:
                    data = self.runtime.dna_molecular_storage.decode_oligo_pool_to_data()
                    text_preview = data.decode("utf-8", errors="replace")[:100]
                    msg = f"Decoded {len(data)} bytes from DNA oligo pool: '{text_preview}'."
                    return RouterResponse(msg, data={"decoded_bytes": len(data), "preview": text_preview})
                except Exception as e:
                    return RouterResponse(f"DNA pool decoding failed: {e}")
            return RouterResponse("DNA molecular storage fabric not available.")

        if lowered in {"/dna-density", "dna-density"}:
            if hasattr(self.runtime, "dna_molecular_storage"):
                density = self.runtime.dna_molecular_storage.compute_theoretical_density_exabytes_per_gram()
                msg = f"Theoretical Single-Stranded DNA Storage Density: {density:.1f} Exabytes per gram."
                return RouterResponse(msg, data={"theoretical_density_eb_per_gram": density})
            return RouterResponse("DNA molecular storage fabric not available.")
"""
    if 'dna-storage-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 244 into router.py')
    else:
        print('Stage 244 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
