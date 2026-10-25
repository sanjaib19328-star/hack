import os
import glob
import csv
import json

targets = ["account_004", "audit_record_6645", "audit_record_5569"]

print("=== 1. Searching for target identifiers across all dataset/ files ===")
occurrences = {t: [] for t in targets}

for root, dirs, files in os.walk("dataset"):
    for f in files:
        path = os.path.join(root, f)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
                for t in targets:
                    if t in content:
                        occurrences[t].append(path)
        except Exception:
            pass

for t, paths in occurrences.items():
    print(f"\nTarget: {t}")
    print(f"Total files found in dataset/: {len(paths)}")
    for p in paths:
        print(f"  - {p}")

print("\n=== 2. Inspecting citations in dataset/sample_output.csv ===")
with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cid = r["case_id"]
        steps = json.loads(r["steps_json"])
        for s in steps:
            res_id = s.get("resource_id", "")
            if res_id in targets:
                print(f"Case: {cid} | Status: {r['deletion_status']} | Step {s['step_no']}: {s}")

print("\n=== 3. Inspecting the actual request & evidence for these cases ===")
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    ev_files = {r["file_id"]: r for r in csv.DictReader(f)}

target_cases = ["case_04", "case_20", "case_25"]
for cid in target_cases:
    req = sample_reqs.get(cid, {})
    print(f"\n--- {cid} ---")
    print(f"Email: {req.get('email')}")
    print(f"Requested At: {req.get('requested_at')}")
    print(f"Reported At: {req.get('reported_at')}")
    print(f"Audit At: {req.get('audit_at')}")
    print(f"Request Text: {req.get('request_text')}")
