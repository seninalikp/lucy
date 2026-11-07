# scripts/create_era22_master_seal.py
import os
import sys
sys.path.insert(0, os.getcwd())

import subprocess
import zipfile
from backend.lucy_core.era22_master_seal import Era22MasterSealFabric

def make_archive(zip_path):
    os.makedirs('archive', exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk('.'):
            if any(p in root.split(os.sep) for p in ['archive', '.git', '__pycache__', '.pytest_cache', 'venv', '.venv']):
                continue
            for f in files:
                if f.endswith('.pyc'):
                    continue
                fp = os.path.join(root, f)
                arcname = os.path.relpath(fp, '.')
                z.write(fp, arcname)
    print(f'Created {zip_path}: {os.path.getsize(zip_path):,} bytes, {len(z.namelist()):,} files')

def main():
    print("Deriving Sovereign Master Seal for Era 22...")
    fabric = Era22MasterSealFabric()
    valid, details = fabric.verify_era22_integrity()
    print("Verification passed    :", valid)
    print("Era 22 Seal ID         :", details["seal_id"])
    print("Creator                :", details["creator"])
    print("Operator               :", details["operator"])
    print("Era 21 Parent Root     :", details["parent_era21_root"])
    print("Era 22 Merkle Root     :", details["era22_merkle_root"])
    print("Master Merkle Root     :", details["master_merkle_root"])
    print("Genesis Signature      :", details["genesis_signature"])

    print("\n[Step 1/3] Generating final code dump...")
    res = subprocess.run([r'C:\Users\admin\AppData\Local\Python\bin\python.exe', 'generate_lucy_code_dump.py'], capture_output=True, text=True)
    print('Code dump summary:', [line for line in res.stdout.splitlines() if 'SUCCESS' in line or 'Total' in line])

    print("\n[Step 2/3] Creating archive/lucy_stage220_era22_master_seal.zip...")
    make_archive('archive/lucy_stage220_era22_master_seal.zip')

    print("\n[Step 3/3] Creating archive/lucy_stage220_era22_sealed.zip...")
    make_archive('archive/lucy_stage220_era22_sealed.zip')

    print("\n" + fabric.format_ascii_status())
    print("\n" + fabric.format_grand_era_report())
    print("=========================================================================")
    print("ERA 22 SOVEREIGN MASTER SEAL & GALACTIC HYPER-MESH GENESIS IMMORTALIZED!")
    print("=========================================================================")

if __name__ == '__main__':
    main()
