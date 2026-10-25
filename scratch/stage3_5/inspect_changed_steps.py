import csv
import json

def load(path):
    d = {}
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            d[r['case_id']] = {
                'status': r['deletion_status'],
                'steps': json.loads(r['steps_json'])
            }
    return d

truth = load('dataset/sample_output.csv')
prev = load('scratch/clean_sample_pred.csv')
latest = load('scratch/candidate_sample_pred.csv')

changed_cases = ['case_06', 'case_07', 'case_08', 'case_09', 'case_10', 'case_18', 'case_20', 'case_22', 'case_23', 'case_25', 'case_28', 'case_29', 'case_31', 'case_32']

for cid in changed_cases:
    print("=" * 80)
    print(f"CASE: {cid} | Prev Status: {prev[cid]['status']} | Latest Status: {latest[cid]['status']} | Truth Status: {truth[cid]['status']}")
    p_steps = prev[cid]['steps']
    l_steps = latest[cid]['steps']
    t_steps = truth[cid]['steps']
    
    # find step removed from prev to latest
    p_set = [json.dumps(s, sort_keys=True) for s in p_steps]
    l_set = [json.dumps(s, sort_keys=True) for s in l_steps]
    
    removed = [s for s in p_steps if json.dumps(s, sort_keys=True) not in l_set]
    added = [s for s in l_steps if json.dumps(s, sort_keys=True) not in p_set]
    
    print(f"Removed from Prev ({len(removed)}):")
    for s in removed:
        print("  -", json.dumps(s))
    print(f"Added to Latest ({len(added)}):")
    for s in added:
        print("  -", json.dumps(s))
        
    print(f"Truth steps ({len(t_steps)}):")
    for s in t_steps:
        print("  T:", json.dumps(s))
