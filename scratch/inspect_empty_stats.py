import csv, json, os, re

# Let's inspect the 60 cases
reqs = {r["case_id"]: r for r in csv.DictReader(open("dataset/deletion_requests.csv", encoding="utf-8"))}
with open("scratch/candidate_output.csv", "r", encoding="utf-8") as f:
    empty_cases = [r for r in csv.DictReader(f) if r["deletion_status"] != "NOT_APPLICABLE" and len(json.loads(r["steps_json"])) == 0]

print(f"Empty non-NA cases count: {len(empty_cases)}")
rep_stat_counts = {}
for r in empty_cases:
    cid = r["case_id"]
    stat = reqs[cid]["reported_status"]
    rep_stat_counts[stat] = rep_stat_counts.get(stat, 0) + 1

print("Reported statuses of empty cases:", rep_stat_counts)
