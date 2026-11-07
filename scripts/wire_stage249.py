"""
scripts/wire_stage249.py
Wires Stage 249 ZeroTrustHardwareEnclaveFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.padic_ultrametric_clusterer import PadicUltrametricClustererFabric, STAGE as STAGE_248\n'
    replacement_import = target_import + 'from backend.lucy_core.zero_trust_hardware_enclave import ZeroTrustHardwareEnclaveFabric, STAGE as STAGE_249\n'
    if 'zero_trust_hardware_enclave' not in text:
        assert target_import in text, 'Target import for Stage 248 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 248: Non-Archimedean p-Adic Ultrametric Cognitive Clustering (Era 25)\n        self.padic_ultrametric_clusterer = PadicUltrametricClustererFabric()\n'
    replacement_init = target_init + '        # Stage 249: Universal Multi-Tier Zero-Trust Hardware Enclave (Era 25)\n        self.zero_trust_hardware_enclave = ZeroTrustHardwareEnclaveFabric()\n'
    if 'self.zero_trust_hardware_enclave' not in text:
        assert target_init in text, 'Target init for Stage 248 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("padic_ultrametric_clusterer", "core"),\n'
    replacement_service = target_service + '            ("zero_trust_hardware_enclave", "core"),\n'
    if '("zero_trust_hardware_enclave", "core")' not in text:
        assert target_service in text, 'Target service for Stage 248 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 249 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /padic-concept <name> <val1> [val2 ...]")\n'
    assert target in text, 'Target end of Stage 248 block not found'

    insertion = """
        # Stage 249: Universal Multi-Tier Zero-Trust Hardware Attestation & Enclave Secure Boot Orchestrator
        if lowered in {"/hw-enclave-status", "hw-enclave-status", "/hardware-enclave-status"}:
            if hasattr(self.runtime, "zero_trust_hardware_enclave"):
                tbl = self.runtime.zero_trust_hardware_enclave.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.zero_trust_hardware_enclave.get_metrics())
            return RouterResponse("Zero-trust hardware enclave not available.")

        if lowered.startswith("/enclave-pcr-extend ") or lowered.startswith("enclave-pcr-extend "):
            if hasattr(self.runtime, "zero_trust_hardware_enclave"):
                parts = raw_text.strip().split(maxsplit=3)
                if len(parts) >= 4:
                    idx = int(parts[1])
                    comp = parts[2]
                    data = parts[3].encode("utf-8")
                    new_val = self.runtime.zero_trust_hardware_enclave.extend_pcr(idx, comp, data)
                    msg = f"Extended PCR[{idx}] ({comp}) -> New Hash: {new_val[:16]}..."
                    return RouterResponse(msg, data={"pcr_index": idx, "component": comp, "hash": new_val})
            return RouterResponse("Usage: /enclave-pcr-extend <pcr_index> <component_name> <measurement_string>")

        if lowered.startswith("/enclave-attest ") or lowered.startswith("enclave-attest "):
            if hasattr(self.runtime, "zero_trust_hardware_enclave"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nonce = parts[1]
                    quote = self.runtime.zero_trust_hardware_enclave.generate_attestation_quote(nonce)
                    valid = self.runtime.zero_trust_hardware_enclave.verify_attestation_quote(quote, nonce)
                    msg = f"Attestation Quote '{quote.quote_id}': verified={valid}, composite={quote.pcr_composite_hex[:16]}..."
                    return RouterResponse(msg, data={"quote_id": quote.quote_id, "verified": valid, "signature": quote.signature_hex})
            return RouterResponse("Usage: /enclave-attest <nonce>")

        if lowered.startswith("/enclave-seal ") or lowered.startswith("enclave-seal "):
            if hasattr(self.runtime, "zero_trust_hardware_enclave"):
                parts = raw_text.strip().split(maxsplit=1)
                if len(parts) >= 2:
                    secret = parts[1].encode("utf-8")
                    package = self.runtime.zero_trust_hardware_enclave.seal_data(secret)
                    msg = f"Sealed payload ({len(secret)} bytes) to PCR composite {package['expected_pcr_composite'][:16]}..."
                    return RouterResponse(msg, data=package)
            return RouterResponse("Usage: /enclave-seal <secret_string>")
"""
    if 'hw-enclave-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 249 into router.py')
    else:
        print('Stage 249 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
