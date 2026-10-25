import csv
import json

truth_file = "dataset/sample_output.csv"
pred_file = "scratch/sample_pred.csv"
req_file = "dataset/sample_deletion_requests.csv"

truth = {r["case_id"]: r for r in csv.DictReader(open(truth_file, encoding="utf-8"))}
pred = {r["case_id"]: r for r in csv.DictReader(open(pred_file, encoding="utf-8"))}
requests = {r["case_id"]: r for r in csv.DictReader(open(req_file, encoding="utf-8"))}

target_cases = ["case_06", "case_08", "case_12", "case_21"]

for cid in target_cases:
    req = requests[cid]
    t = truth[cid]
    p = pred[cid]
    print(f"\n==================== {cid} ====================")
    print(f"Request: {req}")
    print(f"Truth Status: {t['deletion_status']}")
    print(f"Truth Steps ({len(json.loads(t['steps_json']))}):")
    for s in json.loads(t["steps_json"]):
        print(f"  {s}")
    print(f"Pred Status: {p['deletion_status']}")
    print(f"Pred Steps ({len(json.loads(p['steps_json']))}):")
    for s in json.loads(p["steps_json"]):
        print(f"  {s}")
