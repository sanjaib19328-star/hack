import hashlib
import os
import zipfile

files_to_check = [
    'scratch/candidate_output.csv',
    'scratch/stage3_7/patched_code.zip',
    'scratch/stage3_7/patched_main.py',
    'scratch/stage3_9/candidate_final_log.txt',
    'output.csv',
    'code.zip',
    'log.txt',
    'code/main.py'
]

print("=== TASK 3: ARTIFACT CONSISTENCY & CHECKSUM VERIFICATION ===\n")

results = {}
for p in files_to_check:
    if not os.path.exists(p):
        print(f"ERROR: {p} not found!")
        continue
    data = open(p, 'rb').read()
    size = len(data)
    h = hashlib.sha256(data).hexdigest()
    results[p] = {'size': size, 'sha256': h}
    print(f"File: {p}")
    print(f"  Size: {size:,} bytes")
    print(f"  SHA-256: {h}")
    print()

# Check member inside patched_code.zip
zip_path = 'scratch/stage3_7/patched_code.zip'
with zipfile.ZipFile(zip_path, 'r') as z:
    zip_members = z.namelist()
    print(f"Members in {zip_path}: {zip_members}")
    member_data = z.read('code/main.py')
    member_size = len(member_data)
    member_h = hashlib.sha256(member_data).hexdigest()
    print(f"\nMember 'code/main.py' in {zip_path}:")
    print(f"  Size: {member_size:,} bytes")
    print(f"  SHA-256: {member_h}")

patched_source_data = open('scratch/stage3_7/patched_main.py', 'rb').read()
byte_for_byte_match = (member_data == patched_source_data)
print(f"\nByte-for-byte match between 'scratch/stage3_7/patched_main.py' and ZIP member 'code/main.py': {byte_for_byte_match}")
