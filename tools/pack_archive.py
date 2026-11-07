"""
LUCY Stage Archive Packer
Creates a clean zip archive in archive/
"""
import sys
import os
import zipfile

def pack_archive(archive_name):
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    archive_dir = os.path.join(workspace_root, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    
    if not archive_name.endswith(".zip"):
        archive_name += ".zip"
        
    zip_path = os.path.join(archive_dir, archive_name)
    exclude_dirs = {"archive", ".git", "__pycache__", ".pytest_cache", ".gemini"}

    total_files = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(workspace_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f.endswith(".pyc") or f.endswith(".zip"):
                    continue
                full_path = os.path.join(root, f)
                arcname = os.path.relpath(full_path, workspace_root)
                z.write(full_path, arcname)
                total_files += 1

    size = os.path.getsize(zip_path)
    print(f"Archive created: {zip_path} ({size:,} bytes, {total_files} files)")
    return zip_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pack_archive.py <archive_name>")
        sys.exit(1)
    pack_archive(sys.argv[1])
