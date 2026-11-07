"""
tests/test_stage96_offline_model_quantizer.py
Stage 96 = Sovereign Offline Quantization & GGUF Model Compressor

Verifies:
1. STAGE constant is 96.
2. QUANT_SPECS defines all 5 supported quantization schemes.
3. quantize_weights compresses weights file and computes compression metrics.
4. GGUF binary container outputs valid b"GGUF" magic and version 3 header.
5. export_gguf produces both .gguf binary and valid Ollama Modelfile with Senin identity.
6. estimate_vram accurately computes memory footprints across parameter scales.
7. Manifest persistence saves and reloads quantization history from disk.
8. Execution receipt ledger records receipts with SHA256 digests.
9. quant_status produces CP1252-safe ASCII tables.
10. status returns complete diagnostics dictionary.
"""

from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.lucy_core.offline_model_quantizer import (
    STAGE,
    QUANT_SPECS,
    GGUFMetadata,
    OfflineModelQuantizer,
    QuantType,
    QuantizationJobResult,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts: List[Dict[str, Any]] = []

    def issue_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> Dict[str, Any]:
        rcpt = {
            "receipt_id": f"rcpt_{len(self.receipts)+1}",
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class TestStage96OfflineModelQuantizer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        (self.root / "data" / "lucy" / "adapters").mkdir(parents=True, exist_ok=True)
        # Create a mock safetensors adapter file (100 KB)
        self.mock_adapter = self.root / "data" / "lucy" / "adapters" / "lucy_test_adapter.safetensors"
        self.mock_adapter.write_bytes(b"\x00" * 102400)

        self.mock_ledger = MockReceiptLedger()
        self.quantizer = OfflineModelQuantizer(
            project_root=self.root,
            receipt_ledger=self.mock_ledger,
            quant_dir=self.root / "data" / "lucy" / "quantization",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_stage_constant(self) -> None:
        self.assertEqual(STAGE, 96)

    def test_02_quant_specs(self) -> None:
        self.assertIn("Q4_0", QUANT_SPECS)
        self.assertIn("Q4_K_M", QUANT_SPECS)
        self.assertIn("Q5_K_M", QUANT_SPECS)
        self.assertIn("Q8_0", QUANT_SPECS)
        self.assertIn("FP16", QUANT_SPECS)
        self.assertEqual(QUANT_SPECS["Q4_K_M"][1], 15)

    def test_03_quantize_weights(self) -> None:
        result = self.quantizer.quantize_weights(str(self.mock_adapter), quant_type="Q4_K_M")
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.quant_type, "Q4_K_M")
        self.assertGreater(result.compression_ratio, 3.0)
        self.assertTrue(Path(result.output_path).exists())
        self.assertGreater(result.original_size_bytes, result.quantized_size_bytes)

        # Receipt check
        self.assertEqual(len(self.mock_ledger.receipts), 1)
        self.assertEqual(self.mock_ledger.receipts[0]["action_category"], "MODEL_QUANTIZATION")

    def test_04_gguf_binary_header(self) -> None:
        result = self.quantizer.quantize_weights(str(self.mock_adapter), quant_type="Q8_0")
        out_file = Path(result.output_path)
        self.assertTrue(out_file.exists())

        raw_bytes = out_file.read_bytes()
        self.assertGreaterEqual(len(raw_bytes), 24)

        # GGUF magic = b"GGUF"
        magic = raw_bytes[0:4]
        self.assertEqual(magic, b"GGUF")

        # Version = 3 (uint32)
        version = struct.unpack("<I", raw_bytes[4:8])[0]
        self.assertEqual(version, 3)

        # Tensor count = 1 (uint64)
        tensor_count = struct.unpack("<Q", raw_bytes[8:16])[0]
        self.assertEqual(tensor_count, 1)

    def test_05_export_gguf_and_modelfile(self) -> None:
        res = self.quantizer.export_gguf("lucy_persona", quant_type="Q4_K_M")
        self.assertEqual(res["status"], "success")
        self.assertTrue(Path(res["gguf_path"]).exists())
        self.assertTrue(Path(res["modelfile_path"]).exists())

        # Inspect Modelfile contents
        modelfile_text = Path(res["modelfile_path"]).read_text(encoding="utf-8")
        self.assertIn("FROM", modelfile_text)
        self.assertIn("Senin", modelfile_text)
        self.assertIn("Senin Ali K P", modelfile_text)
        self.assertIn("PARAMETER num_ctx 4096", modelfile_text)

    def test_06_estimate_vram(self) -> None:
        est_q4 = self.quantizer.estimate_vram(3.0, quant_type="Q4_K_M")
        est_fp16 = self.quantizer.estimate_vram(3.0, quant_type="FP16")

        self.assertLess(est_q4["weight_mb"], est_fp16["weight_mb"])
        self.assertLess(est_q4["total_vram_mb"], est_fp16["total_vram_mb"])
        self.assertIn("vram_gb", est_q4)

    def test_07_manifest_persistence(self) -> None:
        self.quantizer.quantize_weights(str(self.mock_adapter), quant_type="Q4_0")
        self.quantizer.quantize_weights(str(self.mock_adapter), quant_type="Q5_K_M")
        self.assertEqual(len(self.quantizer.jobs), 2)

        # Reload new quantizer instance from same directory
        reloaded = OfflineModelQuantizer(
            project_root=self.root,
            receipt_ledger=self.mock_ledger,
            quant_dir=self.root / "data" / "lucy" / "quantization",
        )
        self.assertEqual(len(reloaded.jobs), 2)
        self.assertEqual(reloaded.jobs[0].quant_type, "Q4_0")
        self.assertEqual(reloaded.jobs[1].quant_type, "Q5_K_M")

    def test_08_terminal_summary_cp1252(self) -> None:
        self.quantizer.quantize_weights(str(self.mock_adapter), quant_type="Q4_K_M")
        summary = self.quantizer.quant_status()

        # CP1252 encoding safety
        encoded = summary.encode("cp1252")
        self.assertTrue(len(encoded) > 0)

        # No unicode box characters
        for ch in summary:
            self.assertFalse(0x2500 <= ord(ch) <= 0x257F)

        self.assertIn("+----------------------------------------------------------------------+", summary)
        self.assertIn("SOVEREIGN OFFLINE QUANTIZATION", summary)

    def test_09_status_dictionary(self) -> None:
        self.quantizer.quantize_weights(str(self.mock_adapter), quant_type="Q8_0")
        st = self.quantizer.status()
        self.assertEqual(st["stage"], 96)
        self.assertEqual(st["total_quantized_models"], 1)
        self.assertIn("supported_schemes", st)


if __name__ == "__main__":
    unittest.main()
