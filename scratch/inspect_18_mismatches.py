import csv
import json

truth_path = "dataset/sample_output.csv"
pred_path = "scratch/sample_pred.csv"
req_path = "dataset/sample_deletion_requests.csv"

truth = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(open(truth_path, encoding="utf-8"))}
pred = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(open(pred_path, encoding="utf-8"))}
reqs = {r["case_id"]: r for r in csv.DictReader(open(req_path, encoding="utf-8"))}

non_exact_cases = []
for cid in sorted(truth.keys(), key=lambda x: int(x.split('_')[1])):
    if truth[cid] != pred[cid]:
        non_exact_cases.append(cid)

print(f"Total non-exact cases: {len(non_exact_cases)}")
print("Classifying each non-exact case:\n")

for cid in non_exact_cases:
    t_steps = truth[cid]
    p_steps = pred[cid]
    req = reqs[cid]
    
    # Signatures
    # (phase, system_id, resource_id, operation, state)
    t_sem = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in t_steps]
    p_sem = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in p_steps]
    
    # Full with evidence_id
    t_full = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s.get("evidence_id", "")) for s in t_steps]
    p_full = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s.get("evidence_id", "")) for s in p_steps]
    
    mismatch_types = set()
    details = []
    
    # 1. Missing steps (in truth but not pred)
    missing_sem = [s for s in t_sem if s not in p_sem]
    if missing_sem:
        mismatch_types.add("missing step")
        details.append(f"Missing {len(missing_sem)} steps: {[s[1]+':'+s[2]+':'+s[3] for s in missing_sem]}")
        
    # 2. Extra steps (in pred but not truth)
    extra_sem = [s for s in p_sem if s not in t_sem]
    if extra_sem:
        mismatch_types.add("extra step")
        details.append(f"Extra {len(extra_sem)} steps: {[s[1]+':'+s[2]+':'+s[3] for s in extra_sem]}")
        
    # 3. Wrong evidence ID (semantic match exists, but evidence_id differs)
    for p in p_steps:
        # find matching semantic in truth
        p_s = (p["phase"], p["system_id"], p["resource_id"], p["operation"], p["state"])
        matching_t = [t for t in t_steps if (t["phase"], t["system_id"], t["resource_id"], t["operation"], t["state"]) == p_s]
        if matching_t:
            t_ev = matching_t[0].get("evidence_id", "")
            p_ev = p.get("evidence_id", "")
            if t_ev != p_ev:
                mismatch_types.add("wrong evidence ID")
                details.append(f"Evidence ID mismatch on {p['system_id']}:{p['resource_id']}: truth='{t_ev}', pred='{p_ev}'")
                
    # 4. Check ordering/serialization differences
    if len(t_steps) == len(p_steps) and not missing_sem and not extra_sem:
        if t_steps != p_steps:
            mismatch_types.add("ordering or serialization difference")
            details.append("Step ordering differs")

    print(f"[{cid}] (Truth: {len(t_steps)} steps, Pred: {len(p_steps)} steps)")
    print(f"  Classification : {', '.join(sorted(mismatch_types)) if mismatch_types else 'IDENTICAL'}")
    for d in details:
        print(f"    - {d}")
    print()
