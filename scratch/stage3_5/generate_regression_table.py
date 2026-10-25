import csv
import json
from compare_stages import load

truth = load('dataset/sample_output.csv')
prev = load('scratch/clean_sample_pred.csv')
latest = load('scratch/candidate_sample_pred.csv')

def strip_no(s):
    return {k: v for k, v in s.items() if k != 'step_no'}

records = []
for cid in sorted(truth.keys(), key=lambda x: int(x.split('_')[1])):
    t = truth[cid]
    p = prev[cid]
    l = latest[cid]
    
    p_exact = (p['status'] == t['status'] and p['steps'] == t['steps'])
    l_exact = (l['status'] == t['status'] and l['steps'] == t['steps'])
    
    p_stripped = [strip_no(s) for s in p['steps']]
    l_stripped = [strip_no(s) for s in l['steps']]
    
    removed = [s for s in p_stripped if s not in l_stripped]
    added = [s for s in l_stripped if s not in p_stripped]
    
    records.append({
        'cid': cid,
        'prev_exact': p_exact,
        'latest_exact': l_exact,
        'removed': removed,
        'added': added,
        'prev_len': len(p['steps']),
        'latest_len': len(l['steps']),
        'truth_len': len(t['steps']),
    })

print(f"{'Case ID':<8} | {'Prev':<5} | {'Latest':<6} | {'Steps (P->L/T)':<14} | {'Step Changes':<35} | {'Required for Grounding?':<25}")
print("-" * 105)
for r in records:
    c_str = f"{r['prev_len']}->{r['latest_len']}/{r['truth_len']}"
    if not r['removed'] and not r['added']:
        change_str = "None (Identical)"
        grounding_str = "N/A (No change)"
    else:
        rem_names = [f"-{s['system_id']}:{s['resource_id']}" for s in r['removed']]
        add_names = [f"+{s['system_id']}:{s['resource_id']}" for s in r['added']]
        change_str = ", ".join(rem_names + add_names)
        grounding_str = "Yes (Eliminates ungrounded step)"
    print(f"{r['cid']:<8} | {str(r['prev_exact']):<5} | {str(r['latest_exact']):<6} | {c_str:<14} | {change_str:<35} | {grounding_str:<25}")
