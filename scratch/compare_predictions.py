import csv
import json
import os

truth_file = "dataset/sample_output.csv"
pred_file = "scratch/sample_pred.csv"

truth = {}
with open(truth_file, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        truth[row["case_id"]] = {
            "status": row["deletion_status"],
            "steps": json.loads(row["steps_json"])
        }

pred = {}
with open(pred_file, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        pred[row["case_id"]] = {
            "status": row["deletion_status"],
            "steps": json.loads(row["steps_json"])
        }

total = len(truth)
status_matches = 0
exact_steps_matches = 0

mismatches = []

for case_id, t in truth.items():
    p = pred.get(case_id)
    if not p:
        mismatches.append((case_id, "MISSING_IN_PRED", t, None))
        continue
    
    st_match = (t["status"] == p["status"])
    steps_match = (t["steps"] == p["steps"])
    
    if st_match:
        status_matches += 1
    if steps_match:
        exact_steps_matches += 1
    else:
        mismatches.append((case_id, "STEPS_MISMATCH" if st_match else "STATUS_AND_STEPS_MISMATCH", t, p))

print(f"Total sample cases: {total}")
print(f"Status matches: {status_matches} / {total} ({status_matches/total*100:.1f}%)")
print(f"Exact steps matches: {exact_steps_matches} / {total} ({exact_steps_matches/total*100:.1f}%)")
print("\nMismatch Details:")
for cid, reason, t, p in mismatches:
    print(f"\n--- {cid} ({reason}) ---")
    print(f"  Truth status: {t['status']}, Pred status: {p['status']}")
    print(f"  Truth steps ({len(t['steps'])}): {t['steps']}")
    print(f"  Pred steps  ({len(p['steps'])}): {p['steps']}")
