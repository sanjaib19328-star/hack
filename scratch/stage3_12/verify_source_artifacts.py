import hashlib
import os
import sys

expected_artifacts = {
    "scratch/candidate_output.csv": "43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd",
    "scratch/stage3_7/patched_code.zip": "63b2ed2175aa89b6443ff616198b3910cdb8d2fd380f915890005a6e7e1fb818",
    "scratch/stage3_9/candidate_final_log.txt": "ce32768808fbcec57458570f5cf62dc714c11c06932307db0d6ac42bfcf3a56a"
}

print("=== STEP 2: VERIFY APPROVED SOURCE ARTIFACTS ===\n")
all_matched = True

for path, expected_hash in expected_artifacts.items():
    if not os.path.exists(path):
        print(f"[MISSING] {path} does not exist!")
        all_matched = False
        continue
    data = open(path, "rb").read()
    actual_hash = hashlib.sha256(data).hexdigest()
    size = len(data)
    match = (actual_hash.lower() == expected_hash.lower())
    print(f"File: {path}")
    print(f"  Size: {size:,} bytes")
    print(f"  Expected SHA-256: {expected_hash}")
    print(f"  Actual SHA-256:   {actual_hash}")
    print(f"  Match: {match}\n")
    if not match:
        all_matched = False

if not all_matched:
    print("STATUS: BLOCKED - Hash mismatch or missing file!")
    sys.exit(1)
else:
    print("STATUS: PASSED - All approved source artifacts verified bit-for-bit.")
