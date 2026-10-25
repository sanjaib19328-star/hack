import csv
import json

truth_file = "dataset/sample_output.csv"
req_file = "dataset/sample_deletion_requests.csv"
act_file = "dataset/system_activity.csv"

truth = {r["case_id"]: r for r in csv.DictReader(open(truth_file, encoding="utf-8"))}
requests = {r["case_id"]: r for r in csv.DictReader(open(req_file, encoding="utf-8"))}
activities = list(csv.DictReader(open(act_file, encoding="utf-8")))

worker_acts = [
    a for a in activities 
    if a["source_system"] == "deletion_worker" and a["target_system"] == "account_service"
]

print(f"Total worker acts: {len(worker_acts)}")

for cid in sorted(requests.keys(), key=lambda x: int(x.split('_')[1])):
    req = requests[cid]
    t = truth[cid]
    t_steps = json.loads(t["steps_json"])
    t_acc = [s["resource_id"] for s in t_steps if s["system_id"] == "account_service"]
    
    req_at = req["requested_at"]
    rep_at = req["reported_at"]
    
    # Matching worker acts between requested_at and reported_at + 1h
    matching_acts = [
        a for a in worker_acts
        if req_at <= a["event_time"] <= rep_at
    ]
    
    print(f"{cid:<8} | Truth Acc: {t_acc[:1]} | Worker Acts: {[a['resource_id'] + '(' + a['reported_result'] + ')' for a in matching_acts]}")
