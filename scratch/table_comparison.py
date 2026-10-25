import csv
import json

truth_file = "dataset/sample_output.csv"
pred_file = "scratch/sample_pred.csv"

truth = {r["case_id"]: r for r in csv.DictReader(open(truth_file, encoding="utf-8"))}
pred = {r["case_id"]: r for r in csv.DictReader(open(pred_file, encoding="utf-8"))}

print(f"{'Case ID':<10} | {'Truth Stat':<12} | {'Pred Stat':<12} | {'T Steps':<8} | {'P Steps':<8} | {'Mismatch Summary'}")
print("-" * 80)

for cid in sorted(truth.keys(), key=lambda x: int(x.split('_')[1])):
    t = truth[cid]
    p = pred[cid]
    t_st = t["deletion_status"]
    p_st = p["deletion_status"]
    t_steps = json.loads(t["steps_json"])
    p_steps = json.loads(p["steps_json"])
    
    diffs = []
    if t_st != p_st:
        diffs.append(f"Status mismatch: T={t_st} vs P={p_st}")
    
    t_sig = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s.get("evidence_id", "")) for s in t_steps]
    p_sig = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s.get("evidence_id", "")) for s in p_steps]
    
    missing_in_pred = [s for s in t_sig if s not in p_sig]
    extra_in_pred = [s for s in p_sig if s not in t_sig]
    
    if missing_in_pred:
        diffs.append(f"Missing {len(missing_in_pred)}: {[s[1]+':'+s[2]+':'+s[3] for s in missing_in_pred]}")
    if extra_in_pred:
        diffs.append(f"Extra {len(extra_in_pred)}: {[s[1]+':'+s[2]+':'+s[3] for s in extra_in_pred]}")
        
    summary = "MATCH" if not diffs else "; ".join(diffs)
    print(f"{cid:<10} | {t_st:<12} | {p_st:<12} | {len(t_steps):<8} | {len(p_steps):<8} | {summary}")
