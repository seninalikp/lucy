"""
create_folder_lora_archive.py
Creates safety archive zip for the folder creation & LoRA adaptation subsystems.
"""

import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = PROJECT_ROOT / "archive"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_PATH = ARCHIVE_DIR / "lucy_folder_and_lora_verified.zip"

FILES_TO_ARCHIVE = [
    PROJECT_ROOT / "backend" / "lucy_core" / "tools.py",
    PROJECT_ROOT / "backend" / "lucy_core" / "lucy_runtime.py",
    PROJECT_ROOT / "backend" / "lucy_core" / "router.py",
    PROJECT_ROOT / "backend" / "lucy_core" / "natural_action_parser.py",
    PROJECT_ROOT / "backend" / "lucy_core" / "lora_sleep_cycle.py",
    PROJECT_ROOT / "backend" / "lucy_core" / "personal_lora_alignment.py",
    PROJECT_ROOT / "tests" / "test_folder_creation.py",
    PROJECT_ROOT / "tests" / "test_stage42_lora_sleep_cycle.py",
    PROJECT_ROOT / "tests" / "test_stage45_personal_lora_alignment.py",
    PROJECT_ROOT / "scripts" / "test_live_folder_command.py",
    PROJECT_ROOT / "scripts" / "test_live_lora_adaptation.py",
    PROJECT_ROOT / "scripts" / "test_writer_and_folder_integration.py",
]

def main():
    print(f"Creating archive: {ARCHIVE_PATH.name}...")
    with zipfile.ZipFile(ARCHIVE_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in FILES_TO_ARCHIVE:
            if f.exists():
                arcname = f.relative_to(PROJECT_ROOT).as_posix()
                zf.write(f, arcname)
                print(f"  + Added: {arcname} ({f.stat().st_size:,} bytes)")
            else:
                print(f"  ! Missing file: {f}")

    sz = ARCHIVE_PATH.stat().st_size
    print(f"Archive successfully created: {ARCHIVE_PATH} ({sz:,} bytes)")

if __name__ == "__main__":
    main()
