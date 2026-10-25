import csv, json, os

def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

def load_requests(path):
    with open(path, "r", encoding="utf-8") as f:
        return {r["case_id"]: r for r in csv.DictReader(f)}

truth = load_csv("dataset/sample_output.csv")
pred = load_csv("scratch/sample_pred.csv")
reqs = load_requests("dataset/sample_deletion_requests.csv")

non_exact = ['case_01', 'case_03', 'case_04', 'case_09', 'case_18', 'case_19', 'case_20', 'case_21', 'case_22', 'case_23', 'case_25', 'case_26', 'case_27', 'case_28', 'case_29', 'case_31', 'case_32']

for cid in non_exact:
    req = reqs[cid]
    t_stat, t_steps = truth[cid]
    p_stat, p_steps = pred[cid]
    print(f"\n==================== {cid} ====================")
    print(f"Req: email={req.get('email')} req_at={req.get('requested_at')} rep_at={req.get('reported_at')} aud_at={req.get('audit_at')}")
    print(f"Status: truth={t_stat} pred={p_stat}")
    print(f"Truth steps ({len(t_steps)}):")
    for s in t_steps:
        print(f"  T{s['step_no']}: [{s['phase']}] sys={s['system_id']} res={s['resource_id']} op={s['operation']} st={s['state']} ev={s['evidence_id']}")
    print(f"Pred steps ({len(p_steps)}):")
    for s in p_steps:
        print(f"  P{s['step_no']}: [{s['phase']}] sys={s['system_id']} res={s['resource_id']} op={s['operation']} st={s['state']} ev={s['evidence_id']}")
