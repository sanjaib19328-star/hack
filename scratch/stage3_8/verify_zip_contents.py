import zipfile
import hashlib
import os

zip_path = 'scratch/stage3_7/patched_code.zip'

source_mapping = {
    'code/main.py': 'scratch/stage3_7/patched_main.py',
    'code/evaluation/main.py': 'code/evaluation/main.py',
    'code/evaluation/evaluation_report.md': 'code/evaluation/evaluation_report.md',
    'code/evaluation/usage_report.md': 'code/evaluation/usage_report.md',
    'code/evaluation/test_core_engine.py': 'code/evaluation/test_core_engine.py',
    'README.md': 'README.md'
}

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

print(f"Inspecting {zip_path}...")
with zipfile.ZipFile(zip_path, 'r') as z:
    zip_namelist = z.namelist()
    print(f"Total files in ZIP: {len(zip_namelist)}")
    for name in zip_namelist:
        print(f"  - {name}")

    print("\nFile-by-file comparison:")
    print(f"{'Archive Path':<35} | {'Source Path':<35} | {'Zip Size':<9} | {'Src Size':<9} | {'Match?':<6}")
    print("-" * 105)

    all_matched = True
    for arc_path, src_path in source_mapping.items():
        if arc_path not in zip_namelist:
            print(f"MISSING IN ZIP: {arc_path}")
            all_matched = False
            continue

        zip_info = z.getinfo(arc_path)
        zip_bytes = z.read(arc_path)
        zip_hash = sha256_bytes(zip_bytes)
        zip_size = zip_info.file_size

        if not os.path.exists(src_path):
            print(f"SOURCE FILE MISSING: {src_path}")
            all_matched = False
            continue

        src_hash = sha256_file(src_path)
        src_size = os.path.getsize(src_path)

        match = (zip_hash == src_hash and zip_size == src_size)
        if not match:
            all_matched = False

        print(f"{arc_path:<35} | {src_path:<35} | {zip_size:<9} | {src_size:<9} | {str(match):<6}")
        print(f"   ZIP SHA256: {zip_hash}")
        print(f"   SRC SHA256: {src_hash}")

    # Check for any unexpected extra files in the zip
    extra_files = [f for f in zip_namelist if f not in source_mapping]
    if extra_files:
        print(f"\nEXTRA UNEXPECTED FILES IN ZIP: {extra_files}")
        all_matched = False
    else:
        print("\nNo unexpected extra files in ZIP. Exactly the 6 required release files are present.")

    if all_matched:
        print("\nSUCCESS: All files inside scratch/stage3_7/patched_code.zip match their source files 100%!")
    else:
        print("\nFAILURE: Mismatches or missing files detected!")
