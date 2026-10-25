import os
import shutil
import zipfile
import subprocess
import json
import csv

smoke_dir = "scratch/smoke_test_env"
if os.path.exists(smoke_dir):
    shutil.rmtree(smoke_dir)
os.makedirs(smoke_dir)

zip_path = "scratch/candidate_code.zip"
print(f"Extracting {zip_path} into {smoke_dir}...")
with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(smoke_dir)

print("Extracted files:")
for root, dirs, files in os.walk(smoke_dir):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), smoke_dir)
        print(f"  {rel}")

# Prepare mini test dataset (3 diverse cases: complete, incomplete, non-deletion)
mini_input = os.path.join(smoke_dir, "mini_input.csv")
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_rows = list(csv.DictReader(f))

# Include case_01 (complete), case_05 (incomplete), and case_533 (non-deletion from deletion_requests)
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    full_rows = list(csv.DictReader(f))
case_533_row = [r for r in full_rows if r["case_id"] == "case_533"][0]

mini_rows = [sample_rows[0], sample_rows[4], case_533_row]

with open(mini_input, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(mini_rows[0].keys()))
    writer.writeheader()
    writer.writerows(mini_rows)

print(f"\nCreated mini test input with 3 cases: {[r['case_id'] for r in mini_rows]}")

# Copy dataset folder into smoke_dir to simulate full standalone repo root
dest_dataset = os.path.join(smoke_dir, "dataset")
shutil.copytree("dataset", dest_dataset)

# Run code/main.py from within smoke_dir
cmd = ["python", "code/main.py", "mini_input.csv", "mini_output.csv"]
print(f"\nRunning command in {smoke_dir}: {' '.join(cmd)}")
res = subprocess.run(cmd, cwd=smoke_dir, capture_output=True, text=True)

print("STDOUT:")
print(res.stdout)
if res.stderr:
    print("STDERR:")
    print(res.stderr)

mini_output = os.path.join(smoke_dir, "mini_output.csv")
if not os.path.exists(mini_output):
    print("FAILED: mini_output.csv was not created!")
    exit(1)

with open(mini_output, "r", encoding="utf-8") as f:
    out_rows = list(csv.DictReader(f))

print(f"mini_output.csv created with {len(out_rows)} rows:")
for r in out_rows:
    print(f"  {r['case_id']}: {r['deletion_status']} ({len(json.loads(r['steps_json']))} steps)")

# Run schema validation on mini_output.csv
val_cmd = ["python", "code/evaluation/main.py", "--pred", "mini_output.csv", "--expected-count", "3"]
print(f"\nRunning validation in {smoke_dir}: {' '.join(val_cmd)}")
val_res = subprocess.run(val_cmd, cwd=smoke_dir, capture_output=True, text=True)

print("VALIDATION OUTPUT:")
print(val_res.stdout)
if val_res.stderr:
    print("VALIDATION STDERR:")
    print(val_res.stderr)

if "Schema Validation: PASSED" in val_res.stdout:
    print("\nSUCCESS: Smoke test passed with 100% schema compliance!")
else:
    print("\nFAILED: Schema validation failed!")
