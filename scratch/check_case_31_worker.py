import csv
import json
import importlib.util

spec = importlib.util.spec_from_file_location("main", "code/main.py")
main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_mod)

auditor = main_mod.DeletionAuditor("dataset")
req = [r for r in csv.DictReader(open("dataset/sample_deletion_requests.csv", encoding="utf-8")) if r["case_id"] == "case_31"][0]

user_id = auditor.resolver.resolve_email(req["email"])
print(f"case_31 user_id: {user_id}")
print(f"case_31 user_to_account_res: {auditor.user_to_account_res.get(user_id)}")

requested_at = req["requested_at"]
rep_at = req["reported_at"]
rep_stat = req["reported_status"]
w_cands = [
    a for a in auditor.activity_tracker.activities
    if a.get("source_system") == "deletion_worker" and 
       a.get("target_system") == "account_service" and 
       requested_at <= a.get("event_time", "") <= rep_at
]
print(f"w_cands count: {len(w_cands)}")
for a in w_cands:
    print(f"  {a['event_time']} | {a['resource_id']} | {a['reported_result']}")
