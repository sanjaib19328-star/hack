import os
import hashlib
import zipfile

target_files = [
    "code/main.py",
    "code/evaluation/main.py",
    "code/evaluation/evaluation_report.md",
    "code/evaluation/usage_report.md",
    "code/evaluation/test_core_engine.py",
    "README.md"
]

zip_path = "scratch/candidate_code.zip"

def get_file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_zip_entry_sha256(z, arcname):
    h = hashlib.sha256()
    with z.open(arcname) as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

print("=== Comparing Working Tree Files vs Candidate ZIP Entries ===")
all_match = True

if not os.path.exists(zip_path):
    print(f"ERROR: {zip_path} does not exist!")
    exit(1)

with zipfile.ZipFile(zip_path, "r") as z:
    zip_entries = {info.filename: info for info in z.infolist()}
    
    print(f"{'File Path':<40} {'Disk Size':<10} {'ZIP Size':<10} {'Disk SHA256 (first 12)':<15} {'ZIP SHA256 (first 12)':<15} {'Match?'}")
    print("-" * 105)
    
    for fpath in target_files:
        arcname = fpath.replace("\\", "/")
        disk_size = os.path.getsize(fpath)
        disk_hash = get_file_sha256(fpath)
        
        if arcname not in zip_entries:
            print(f"{arcname:<40} {disk_size:<10} {'MISSING':<10} {disk_hash[:12]:<15} {'N/A':<15} FAIL")
            all_match = False
            continue
            
        zip_size = zip_entries[arcname].file_size
        zip_hash = get_zip_entry_sha256(z, arcname)
        
        match = (disk_size == zip_size) and (disk_hash == zip_hash)
        if not match:
            all_match = False
            
        print(f"{arcname:<40} {disk_size:<10} {zip_size:<10} {disk_hash[:12]:<15} {zip_hash[:12]:<15} {'OK' if match else 'MISMATCH'}")
        print(f"  -> Full Disk Hash: {disk_hash}")
        print(f"  -> Full ZIP  Hash: {zip_hash}")

print("\nResult:", "ALL FILES MATCH PERFECTLY" if all_match else "MISMATCH DETECTED")
