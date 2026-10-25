import csv, json, os

def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

truth = load_csv("dataset/sample_output.csv")
pred = load_csv("scratch/sample_pred.csv")
reqs = {r["case_id"]: r for r in csv.DictReader(open("dataset/sample_deletion_requests.csv", encoding="utf-8"))}

cases = ['case_01', 'case_03', 'case_04', 'case_09', 'case_18', 'case_19', 'case_20', 'case_21', 'case_22', 'case_23', 'case_25', 'case_26', 'case_27', 'case_28', 'case_29', 'case_31', 'case_32']

print(f"Investigating {len(cases)} cases...")

for cid in cases:
    t_stat, t_steps = truth[cid]
    p_stat, p_steps = pred[cid]
    req = reqs[cid]
    
    # Classify diffs
    t_set = {(s['phase'], s['system_id'], s['resource_id'], s['operation'], s['state']) for s in t_steps}
    p_set = {(s['phase'], s['system_id'], s['resource_id'], s['operation'], s['state']) for s in p_steps}
    
    missing = [s for s in t_steps if (s['phase'], s['system_id'], s['resource_id'], s['operation'], s['state']) not in p_set]
    extra = [s for s in p_steps if (s['phase'], s['system_id'], s['resource_id'], s['operation'], s['state']) not in t_set]
    
    # Check evidence differences for matching steps
    ev_diffs = []
    for s_p in p_steps:
        for s_t in t_steps:
            if (s_p['phase'], s_p['system_id'], s_p['resource_id'], s_p['operation'], s_p['state']) == \
               (s_t['phase'], s_t['system_id'], s_t['resource_id'], s_t['operation'], s_t['state']):
                if s_p['evidence_id'] != s_t['evidence_id']:
                    ev_diffs.append((s_p['resource_id'], s_t['evidence_id'], s_p['evidence_id']))
                    
    print(f"\n=======================================================")
    print(f"CASE: {cid} | User: {req['email']} | ReqAt: {req['requested_at']} | Status: {t_stat}")
    print(f"Missing steps in Pred ({len(missing)}):")
    for m in missing:
        print(f"  - [{m['phase']}] sys={m['system_id']} res={m['resource_id']} op={m['operation']} st={m['state']} ev={m['evidence_id']}")
    print(f"Extra steps in Pred ({len(extra)}):")
    for e in extra:
        print(f"  + [{e['phase']}] sys={e['system_id']} res={e['resource_id']} op={e['operation']} st={e['state']} ev={e['evidence_id']}")
    if ev_diffs:
        print(f"Evidence ID differences ({len(ev_diffs)}):")
        for res, t_ev, p_ev in ev_diffs:
            print(f"  * {res}: Truth={t_ev} vs Pred={p_ev}")
