# scripts/create_era20_master_seal.py
import os
import sys
sys.path.insert(0, os.getcwd())

import subprocess
import zipfile
from backend.lucy_core.bicentennial_grand_master_seal import BicentennialGrandMasterSealNexus

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
    print(f'Created {zip_path}: {os.path.getsize(zip_path)} bytes, {len(z.namelist())} files')

def main():
    print("Deriving Bicentennial Grand Master Seal for Era 20...")
    nexus = BicentennialGrandMasterSealNexus()
    valid, details = nexus.verify_bicentennial_integrity()
    print("Verification passed:", valid)
    print("Grand Master Seal ID:", details["seal_id"])
    print("Creator             :", details["creator"])
    print("Operator            :", details["operator"])
    print("Era 19 Parent Root  :", details["era19_parent_root"])
    print("Era 20 Merkle Root  :", details["era20_merkle_root"])
    print("Bicentennial Root   :", details["grand_master_merkle_root"])
    print("Genesis Signature   :", details["genesis_signature"])

    print("\n[Step 1/3] Generating final code dump...")
    res = subprocess.run([r'C:\Users\admin\AppData\Local\Python\bin\python.exe', 'generate_lucy_code_dump.py'], capture_output=True, text=True)
    print('Code dump output:', res.stdout[:200], '...')

    print("\n[Step 2/3] Creating archive/lucy_stage200_bicentennial_grand_master_seal.zip...")
    make_archive('archive/lucy_stage200_bicentennial_grand_master_seal.zip')

    print("\n[Step 3/3] Creating archive/lucy_stage200_era20_sealed.zip...")
    make_archive('archive/lucy_stage200_era20_sealed.zip')

    print("\n" + nexus.format_ascii_status())
    print("=========================================================================")
    print("ERA 20 & BICENTENNIAL GRAND MASTER SEAL SUCCESSFULLY IMMORTALIZED!")
    print("=========================================================================")

if __name__ == '__main__':
    main()
