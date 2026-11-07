"""
tests/test_stage106_offline_voice_fabric.py
Stage 106: Offline Multi-Modal Voice Fabric Unit Tests
"""

import io
import os
import shutil
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from backend.lucy_core.offline_voice_fabric import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    DEFAULT_SAMPLE_RATE,
    STAGE,
    AudioPacket,
    OfflineVoiceFabric,
    TranscriptionResult,
    VoiceProfile,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category, operation, target, verified_outcome):
        rec = {
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        }
        self.receipts.append(rec)
        return rec


class TestStage106OfflineVoiceFabric(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage106_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 106)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertEqual(DEFAULT_SAMPLE_RATE, 16000)

    def test_02_synthesize_speech_wav_format(self):
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
        )
        wav_bytes, packet = fabric.synthesize_speech("Hello Senin, Lucy OS is fully online.")
        self.assertTrue(wav_bytes.startswith(b"RIFF"))
        self.assertIn(b"WAVE", wav_bytes[:16])
        self.assertIsInstance(packet, AudioPacket)
        self.assertGreater(packet.duration_sec, 0.4)
        self.assertGreater(packet.data_size_bytes, 1000)

    def test_03_wav_playback_validation(self):
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
        )
        wav_bytes, _ = fabric.synthesize_speech("Testing acoustic RIFF stream.")
        with wave.open(io.BytesIO(wav_bytes), "rb") as r:
            self.assertEqual(r.getnchannels(), 1)
            self.assertEqual(r.getsampwidth(), 2)
            self.assertEqual(r.getframerate(), 16000)
            frames = r.readframes(r.getnframes())
            self.assertGreater(len(frames), 0)

    def test_04_energy_calculation(self):
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
        )
        # Quiet PCM (all zeros)
        quiet_pcm = struct.pack("<1000h", *([0] * 1000))
        e_quiet = fabric.compute_audio_energy(quiet_pcm)
        self.assertEqual(e_quiet, 0.0)

        # Loud PCM (high amplitude)
        loud_pcm = struct.pack("<1000h", *([15000] * 1000))
        e_loud = fabric.compute_audio_energy(loud_pcm)
        self.assertGreater(e_loud, 0.1)

    def test_05_vad_evaluation(self):
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
        )
        wav_bytes, _ = fabric.synthesize_speech("Voice activity test phrase.")
        is_speech, energy = fabric.evaluate_vad(wav_bytes)
        self.assertTrue(is_speech)
        self.assertGreater(energy, fabric.energy_threshold)

        # Silence test
        silence_wav = struct.pack("<44s1000h", b"RIFF" + b"\x00" * 40, *([0] * 1000))
        is_silent, e_silent = fabric.evaluate_vad(silence_wav)
        self.assertFalse(is_silent)
        self.assertLess(e_silent, fabric.energy_threshold)

    def test_06_transcribe_audio_speech(self):
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
        )
        wav_bytes, _ = fabric.synthesize_speech("System status online.")
        res = fabric.transcribe_audio(wav_bytes, simulated_text="System status online.")
        self.assertIsInstance(res, TranscriptionResult)
        self.assertTrue(res.vad_triggered)
        self.assertEqual(res.text, "System status online.")
        self.assertGreater(res.confidence, 0.8)

    def test_07_transcribe_silence(self):
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
        )
        silence_bytes = struct.pack("<1000h", *([0] * 1000))
        res = fabric.transcribe_audio(silence_bytes)
        self.assertFalse(res.vad_triggered)
        self.assertIn("Below VAD Threshold", res.text)

    def test_08_tune_vad_parameters(self):
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
        )
        tuned = fabric.tune_vad(energy_threshold=0.08, silence_window_ms=600)
        self.assertEqual(tuned["energy_threshold"], 0.08)
        self.assertEqual(tuned["silence_window_ms"], 600)
        self.assertEqual(tuned["status"], "CALIBRATED")

        # Persistence check
        reloaded = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
        )
        self.assertEqual(reloaded.energy_threshold, 0.08)
        self.assertEqual(reloaded.silence_window_ms, 600)

    def test_09_voice_profile_customization(self):
        custom_prof = VoiceProfile(
            name="Lucy-Sovereign",
            pitch=1.2,
            speed=1.1,
            volume=0.85,
        )
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
            profile=custom_prof,
        )
        _, packet = fabric.synthesize_speech("Calibrated sovereign voice.")
        self.assertEqual(fabric.profile.name, "Lucy-Sovereign")
        self.assertEqual(fabric.profile.pitch, 1.2)

    def test_10_receipt_ledger_integration(self):
        ledger = MockReceiptLedger()
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            receipt_ledger=ledger,
            data_dir=self.temp_path / "voice",
        )
        wav_bytes, _ = fabric.synthesize_speech("Receipt test speech.")
        fabric.transcribe_audio(wav_bytes)
        fabric.tune_vad(energy_threshold=0.05)

        categories = [r["category"] for r in ledger.receipts]
        self.assertIn("VOICE_SYNTHESIS", categories)
        self.assertIn("VOICE_TRANSCRIPTION", categories)
        self.assertIn("VOICE_VAD_TRIGGER", categories)

    def test_11_cp1252_voice_status_table(self):
        fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            data_dir=self.temp_path / "voice",
        )
        fabric.synthesize_speech("Dashboard status test phrase.")
        status_table = fabric.voice_status()
        self.assertIn("LUCY OS - OFFLINE MULTI-MODAL VOICE FABRIC", status_table)
        self.assertIn("STAGE 106: SOVEREIGN LOCAL SPEECH ENGINE", status_table)
        status_table.encode("cp1252")

        st = fabric.status()
        self.assertEqual(st["stage"], 106)
        self.assertEqual(st["creator"], "Senin")
        self.assertTrue(st["sovereign_offline"])


if __name__ == "__main__":
    unittest.main()
