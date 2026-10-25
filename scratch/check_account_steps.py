import csv
import json
import re

with open("scratch/candidate_output.csv", "r", encoding="utf-8") as f:
    cand_518 = list(csv.DictReader(f))

with open("scratch/candidate_sample_pred.csv", "r", encoding="utf-8") as f:
    cand_32 = list(csv.DictReader(f))

# Let's inspect the account_service steps in cand_32
print("Account service steps in cand_32 (sample cases):")
for r in cand_32:
    steps = json.loads(r["steps_json"])
    acc_steps = [s for s in steps if s["system_id"] == "account_service"]
    if acc_steps:
        print(f"  {r['case_id']} ({r['deletion_status']}): {[s['resource_id'] for s in acc_steps]}")

# Let's inspect how many cases in cand_518 have account_service steps:
acc_518_count = 0
for r in cand_518:
    steps = json.loads(r["steps_json"])
    if any(s["system_id"] == "account_service" for s in steps):
        acc_518_count += 1

print(f"\nTotal cases in 518 dataset with account_service steps: {acc_518_count}/{len(cand_518)}")
