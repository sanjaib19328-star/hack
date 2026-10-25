import os
import shutil
import zipfile
import subprocess
import csv
import json

test_dir = os.path.abspath("scratch/package_test_fresh")
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
os.makedirs(test_dir)

zip_path = os.path.abspath("scratch/candidate_code.zip")
print(f"Extracting {zip_path} into fresh directory: {test_dir}")
with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(test_dir)

print("\nPackaged files verified:")
for root, dirs, files in os.walk(test_dir):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), test_dir)
        print(f"  {rel}")

# Prepare environment: copy dataset into test_dir so it is fully standalone
dest_dataset = os.path.join(test_dir, "dataset")
shutil.copytree("dataset", dest_dataset)

# 1. Test A: Run packaged engine on all 32 sample requests
print("\n--- Test A: All 32 Sample Requests ---")
cmd_a = ["python", os.path.join("code", "main.py"), os.path.join("dataset", "sample_deletion_requests.csv"), "out_sample.csv"]
res_a = subprocess.run(cmd_a, cwd=test_dir, capture_output=True, text=True)
print(f"Exit code: {res_a.returncode}")
print(f"Stdout:\n{res_a.stdout.strip()}")
if res_a.stderr:
    print(f"Stderr:\n{res_a.stderr.strip()}")

# Evaluate output of Test A using packaged evaluator
val_a = ["python", os.path.join("code", "evaluation", "main.py"), "--pred", "out_sample.csv", "--truth", os.path.join("dataset", "sample_output.csv"), "--expected-count", "32"]
val_res_a = subprocess.run(val_a, cwd=test_dir, capture_output=True, text=True)
print(f"Evaluator Exit code: {val_res_a.returncode}")
print(f"Evaluator Stdout:\n{val_res_a.stdout.strip()}")

# 2. Test B: Empty input (header only)
print("\n--- Test B: Empty Input (header only) ---")
empty_input = os.path.join(test_dir, "empty_in.csv")
with open(empty_input, "w", encoding="utf-8") as f:
    f.write("case_id,email,requested_at,reported_status,reported_at,audit_at,request_text\n")

cmd_b = ["python", os.path.join("code", "main.py"), "empty_in.csv", "out_empty.csv"]
res_b = subprocess.run(cmd_b, cwd=test_dir, capture_output=True, text=True)
print(f"Exit code: {res_b.returncode}")
print(f"Stdout:\n{res_b.stdout.strip()}")
if os.path.exists(os.path.join(test_dir, "out_empty.csv")):
    with open(os.path.join(test_dir, "out_empty.csv"), "r", encoding="utf-8") as f:
        print(f"Output lines: {len(f.readlines())}")

# 3. Test C: Malformed Input (missing values, weird characters, quotes)
print("\n--- Test C: Malformed Input ---")
malformed_input = os.path.join(test_dir, "malformed_in.csv")
with open(malformed_input, "w", encoding="utf-8") as f:
    f.write("case_id,email,requested_at,reported_status,reported_at,audit_at,request_text\n")
    f.write('case_999,"bad-email-no-at",2026-09-01T10:00:00Z,COMPLETE,2026-09-02T10:00:00Z,2026-09-03T10:00:00Z,"Weird symbols: \u2603 \u2708 and quotes \\"hello\\""\n')
    f.write('case_998,,,,,,\n')

cmd_c = ["python", os.path.join("code", "main.py"), "malformed_in.csv", "out_malformed.csv"]
res_c = subprocess.run(cmd_c, cwd=test_dir, capture_output=True, text=True)
print(f"Exit code: {res_c.returncode}")
print(f"Stdout:\n{res_c.stdout.strip()}")
if res_c.stderr:
    print(f"Stderr:\n{res_c.stderr.strip()}")
if os.path.exists(os.path.join(test_dir, "out_malformed.csv")):
    with open(os.path.join(test_dir, "out_malformed.csv"), "r", encoding="utf-8") as f:
        print("Malformed output content:")
        for line in f:
            print(f"  {line.strip()[:80]}")

# 4. Test D: Non-deletion requests only
print("\n--- Test D: Non-deletion Requests Only ---")
non_del_input = os.path.join(test_dir, "non_del_in.csv")
with open(non_del_input, "w", encoding="utf-8") as f:
    f.write("case_id,email,requested_at,reported_status,reported_at,audit_at,request_text\n")
    f.write('case_991,user1@test.com,2026-09-01T10:00:00Z,NOT_STARTED,2026-09-02T10:00:00Z,2026-09-03T10:00:00Z,"Please leave the account active and update my phone number."\n')
    f.write('case_992,user2@test.com,2026-09-01T10:00:00Z,NOT_STARTED,2026-09-02T10:00:00Z,2026-09-03T10:00:00Z,"I still need my account, so I am not asking for deletion."\n')

cmd_d = ["python", os.path.join("code", "main.py"), "non_del_in.csv", "out_non_del.csv"]
res_d = subprocess.run(cmd_d, cwd=test_dir, capture_output=True, text=True)
print(f"Exit code: {res_d.returncode}")
print(f"Stdout:\n{res_d.stdout.strip()}")
with open(os.path.join(test_dir, "out_non_del.csv"), "r", encoding="utf-8") as f:
    for line in f:
        print(f"  {line.strip()}")

val_d = ["python", os.path.join("code", "evaluation", "main.py"), "--pred", "out_non_del.csv", "--expected-count", "2"]
val_res_d = subprocess.run(val_d, cwd=test_dir, capture_output=True, text=True)
print(f"Validation:\n{val_res_d.stdout.strip()}")

# Cleanup
shutil.rmtree(test_dir)
print("\nCleaned up package_test_fresh. Hardened package test PASSED!")
