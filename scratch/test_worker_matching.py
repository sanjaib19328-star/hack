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

correct = 0
total_with_acc = 0

for cid in sorted(requests.keys(), key=lambda x: int(x.split('_')[1])):
    req = requests[cid]
    t = truth[cid]
    t_steps = json.loads(t["steps_json"])
    t_acc = [s["resource_id"] for s in t_steps if s["system_id"] == "account_service"]
    if not t_acc:
        continue
    total_with_acc += 1
    target = t_acc[0]
    
    req_at = req["requested_at"]
    rep_at = req["reported_at"]
    rep_stat = req["reported_status"]
    
    # filter worker acts in [requested_at, reported_at]
    cands = [a for a in worker_acts if req_at <= a["event_time"] <= rep_at]
    # filter by matching status if possible
    # COMPLETE -> SUCCESS, PARTIALLY_COMPLETE -> PARTIAL / FAILED
    status_match = [
        a for a in cands 
        if (rep_stat == "COMPLETE" and a["reported_result"] == "SUCCESS") or
           (rep_stat == "PARTIALLY_COMPLETE" and a["reported_result"] in ("PARTIAL", "FAILED"))
    ]
    
    cand_ids = [a["resource_id"] for a in (status_match or cands)]
    if target in cand_ids:
        correct += 1
    print(f"{cid:<8} | Target: {target:<12} | Found in cands? {target in cand_ids} | Cands: {cand_ids}")

print(f"\nWorker correlation coverage: {correct}/{total_with_acc} ({correct/total_with_acc*100:.1f}%)")
