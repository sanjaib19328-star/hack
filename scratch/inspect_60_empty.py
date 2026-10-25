import csv, json

with open("scratch/candidate_output.csv", "r", encoding="utf-8") as f:
    empty_cases = [r for r in csv.DictReader(f) if r["deletion_status"] != "NOT_APPLICABLE" and len(json.loads(r["steps_json"])) == 0]

reqs = {r["case_id"]: r for r in csv.DictReader(open("dataset/deletion_requests.csv", encoding="utf-8"))}

print(f"Total empty non-NA cases: {len(empty_cases)}")
for r in empty_cases[:15]:
    cid = r["case_id"]
    req = reqs[cid]
    print(f"{cid}: rep_stat={req['reported_status']} req_at={req['requested_at']} aud_at={req['audit_at']} email={req['email']}")
