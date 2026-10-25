import csv
import json

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("scratch/candidate_sample_pred.csv", "r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

non_exact_cases = []
for cid in truth:
    t_stat, t_steps = truth[cid]
    p_stat, p_steps = pred[cid]
    if t_stat != p_stat or t_steps != p_steps:
        non_exact_cases.append(cid)

print(f"Total non-exact cases: {len(non_exact_cases)}")
print("Cases:", non_exact_cases)

def step_str(s):
    return f"{s.get('phase')} | {s.get('system_id')} | {s.get('resource_id')} | {s.get('operation')} | {s.get('state')} | ev:'{s.get('evidence_id')}'"

for cid in non_exact_cases:
    t_stat, t_steps = truth[cid]
    p_stat, p_steps = pred[cid]
    
    t_keys = [(s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"), s.get("evidence_id")) for s in t_steps]
    p_keys = [(s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"), s.get("evidence_id")) for s in p_steps]
    
    missing_in_pred = [s for s in t_steps if (s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"), s.get("evidence_id")) not in p_keys]
    extra_in_pred = [s for s in p_steps if (s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"), s.get("evidence_id")) not in t_keys]
    
    print(f"\n=======================================================")
    print(f"CASE: {cid} | Truth Status: {t_stat} ({len(t_steps)} steps) | Pred Status: {p_stat} ({len(p_steps)} steps)")
    
    print("Truth Steps:")
    for s in t_steps:
        print(f"  T{s['step_no']}: {step_str(s)}")
        
    print("Pred Steps:")
    for s in p_steps:
        print(f"  P{s['step_no']}: {step_str(s)}")
        
    print("Missing Truth Steps in Pred:")
    for s in missing_in_pred:
        print(f"  - {step_str(s)}")
        
    print("Extra Pred Steps in Pred:")
    for s in extra_in_pred:
        print(f"  + {step_str(s)}")
