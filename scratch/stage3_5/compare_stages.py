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

print(f"{'Case ID':<10} | {'Prev Exact':<11} | {'Latest Exact':<13} | {'Prev Steps':<11} | {'Latest Steps':<13} | {'Truth Steps':<12} | {'Diff / Status'}")
print("-" * 90)

changed_cases = []
for cid in sorted(truth.keys(), key=lambda x: int(x.split('_')[1])):
    t = truth[cid]
    p = prev[cid]
    l = latest[cid]
    
    p_exact = (p['status'] == t['status'] and p['steps'] == t['steps'])
    l_exact = (l['status'] == t['status'] and l['steps'] == t['steps'])
    
    diff_note = ""
    if p['steps'] != l['steps'] or p['status'] != l['status']:
        diff_note = "CHANGED"
        changed_cases.append(cid)
    else:
        diff_note = "IDENTICAL"
        
    print(f"{cid:<10} | {str(p_exact):<11} | {str(l_exact):<13} | {len(p['steps']):<11} | {len(l['steps']):<13} | {len(t['steps']):<12} | {diff_note}")

print("\nChanged cases count:", len(changed_cases))
print("Changed cases:", changed_cases)
