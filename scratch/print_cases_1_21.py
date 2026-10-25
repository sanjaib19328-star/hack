import csv
import json

truth_file = "dataset/sample_output.csv"
pred_file = "scratch/sample_pred.csv"

truth = {r["case_id"]: r for r in csv.DictReader(open(truth_file, encoding="utf-8"))}
pred = {r["case_id"]: r for r in csv.DictReader(open(pred_file, encoding="utf-8"))}

for i in range(1, 22):
    cid = f"case_{i:02d}"
    t = truth[cid]
    p = pred[cid]
    t_st = t["deletion_status"]
    p_st = p["deletion_status"]
    t_steps = json.loads(t["steps_json"])
    p_steps = json.loads(p["steps_json"])
    
    diffs = []
    if t_st != p_st:
        diffs.append(f"STATUS MISMATCH (T={t_st}, P={p_st})")
    
    t_sig = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in t_steps]
    p_sig = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in p_steps]
    
    missing = [s for s in t_sig if s not in p_sig]
    extra = [s for s in p_sig if s not in t_sig]
    if missing:
        diffs.append(f"Missing {len(missing)}")
    if extra:
        diffs.append(f"Extra {len(extra)}")
    
    match_str = "EXACT MATCH" if (t_st == p_st and not missing and not extra) else "; ".join(diffs)
    print(f"{cid:<8} | Truth={t_st:<11} Pred={p_st:<11} | T={len(t_steps)} P={len(p_steps)} | {match_str}")
