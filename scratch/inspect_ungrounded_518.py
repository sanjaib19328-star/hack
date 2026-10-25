import csv
import json

with open("scratch/candidate_output.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# Check which cases only have an account_service step and nothing else
only_account_cases = []
for r in rows:
    steps = json.loads(r["steps_json"])
    if len(steps) > 0 and all(s["system_id"] == "account_service" for s in steps):
        only_account_cases.append((r["case_id"], r["deletion_status"], [s["resource_id"] for s in steps]))

print(f"Total cases with ONLY account_service steps in 518 dataset: {len(only_account_cases)}")
print("Sample first 10:")
for c in only_account_cases[:10]:
    print(" ", c)
