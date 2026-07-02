import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.recovery import RecoveryReference


class RecoveryReferenceTests(unittest.TestCase):
    def test_loads_recovered_checkpoint_map(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "recovered_architecture.json").write_text(
                json.dumps(
                    {
                        "source": "test",
                        "highest_recovered_checkpoint": "023",
                        "confidence": "reference_only",
                        "checkpoints": [{"checkpoint": "023", "desc": "Recovered"}],
                    }
                ),
                encoding="utf-8",
            )
            recovery = RecoveryReference(root)
            summary = recovery.summary()
            self.assertEqual(summary["highest_recovered_checkpoint"], "023")
            self.assertEqual(summary["checkpoint_count"], 1)


if __name__ == "__main__":
    unittest.main()
