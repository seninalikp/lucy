"""
scripts/wire_stage232.py
Wires Stage 232 LatticePQCVaultFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.neuromorphic_spiking_fabric import NeuromorphicSpikingFabric, STAGE as STAGE_231\n'
    replacement_import = target_import + 'from backend.lucy_core.lattice_pqc_vault import LatticePQCVaultFabric, STAGE as STAGE_232\n'
    if 'lattice_pqc_vault' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 231: Neuromorphic Spiking Neural Network & LIF Synaptic Fabric (Era 24)\n        self.neuromorphic_spiking = NeuromorphicSpikingFabric()\n'
    replacement_init = target_init + '        # Stage 232: Quantum-Resilient Lattice Post-Quantum Cryptography Vault (Era 24)\n        self.lattice_pqc_vault = LatticePQCVaultFabric()\n'
    if 'self.lattice_pqc_vault' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("neuromorphic_spiking", "core"),\n'
    replacement_service = target_service + '            ("lattice_pqc_vault", "core"),\n'
    if '("lattice_pqc_vault", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 232 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '            return RouterResponse("Usage: /snn-sim <duration_ms>")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 232: Quantum-Resilient Lattice Post-Quantum Cryptography Vault
        if lowered in {"/lattice-vault-status", "lattice-vault-status", "/pqc-vault-status", "pqc-vault-status"}:
            if hasattr(self.runtime, "lattice_pqc_vault"):
                tbl = self.runtime.lattice_pqc_vault.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.lattice_pqc_vault.status())
            return RouterResponse("Lattice PQC vault not available.")

        if lowered.startswith("/lattice-encapsulate ") or lowered.startswith("lattice-encapsulate "):
            if hasattr(self.runtime, "lattice_pqc_vault"):
                parts = raw_text.strip().split()
                kid = parts[1] if len(parts) >= 2 else "sovereign_master_pqc_key"
                try:
                    ct, sh = self.runtime.lattice_pqc_vault.encapsulate(kid)
                    msg = f"Kyber-style PQC encapsulation complete for key '{kid}'. Shared Key Hash: {sh[:16]}..."
                    return RouterResponse(msg, data={"key_id": kid, "shared_key": sh, "ct_u_norm": sum(ct.u)})
                except Exception as e:
                    return RouterResponse(f"PQC Encapsulation failed: {e}")
            return RouterResponse("Lattice PQC vault not available.")

        if lowered.startswith("/lattice-vault-store ") or lowered.startswith("lattice-vault-store "):
            if hasattr(self.runtime, "lattice_pqc_vault"):
                parts = raw_text.strip().split(maxsplit=2)
                if len(parts) >= 3:
                    rec_id, s_text = parts[1], parts[2]
                    try:
                        rec = self.runtime.lattice_pqc_vault.store_encrypted_vault_secret("sovereign_master_pqc_key", rec_id, s_text)
                        msg = f"Quantum-safely stored record '{rec_id}' in lattice PQC vault ({rec['payload_len']} bytes encrypted)."
                        return RouterResponse(msg, data=rec)
                    except Exception as e:
                        return RouterResponse(f"Vault store failed: {e}")
            return RouterResponse("Usage: /lattice-vault-store <record_id> <secret_text>")

        if lowered.startswith("/lattice-vault-read ") or lowered.startswith("lattice-vault-read "):
            if hasattr(self.runtime, "lattice_pqc_vault"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    rec_id = parts[1]
                    try:
                        dec = self.runtime.lattice_pqc_vault.retrieve_decrypted_vault_secret(rec_id)
                        msg = f"Decrypted record '{rec_id}': '{dec}'"
                        return RouterResponse(msg, data={"record_id": rec_id, "decrypted_text": dec})
                    except Exception as e:
                        return RouterResponse(f"Vault read failed: {e}")
            return RouterResponse("Usage: /lattice-vault-read <record_id>")
"""
    if 'lattice-vault-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 232 into router.py')
    else:
        print('Stage 232 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
