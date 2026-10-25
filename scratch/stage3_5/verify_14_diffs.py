import json
from compare_stages import load

prev = load('scratch/clean_sample_pred.csv')
latest = load('scratch/candidate_sample_pred.csv')
changed_cases = ['case_06', 'case_07', 'case_08', 'case_09', 'case_10', 'case_18', 'case_20', 'case_22', 'case_23', 'case_25', 'case_28', 'case_29', 'case_31', 'case_32']

def strip_no(s):
    return {k: v for k, v in s.items() if k != 'step_no'}

print("Detailed check of differences for all 14 changed cases:")
for cid in changed_cases:
    p_steps = prev[cid]['steps']
    l_steps = latest[cid]['steps']
    p_stripped = [strip_no(s) for s in p_steps]
    l_stripped = [strip_no(s) for s in l_steps]
    diff = [s for s in p_stripped if s not in l_stripped]
    added = [s for s in l_stripped if s not in p_stripped]
    print(f"{cid}: len prev={len(p_steps)}, len latest={len(l_steps)}, diff_removed={len(diff)}, diff_added={len(added)}")
    for d in diff:
        print(f"   Removed: sys={d['system_id']}, res={d['resource_id']}, op={d['operation']}, state={d['state']}")
    for a in added:
        print(f"   Added: sys={a['system_id']}, res={a['resource_id']}, op={a['operation']}, state={a['state']}")
