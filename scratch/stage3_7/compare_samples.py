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

cand = load('scratch/candidate_sample_pred.csv')
test = load('scratch/stage3_7/test_sample_pred.csv')
truth = load('dataset/sample_output.csv')

print(f"{'Case ID':<8} | {'Candidate Steps':<16} | {'Patched Steps':<14} | {'Truth Steps':<12} | {'Diff / Notes'}")
print("-" * 80)

diffs = []
for cid in sorted(truth.keys(), key=lambda x: int(x.split('_')[1])):
    c_data = cand[cid]
    t_data = test[cid]
    truth_data = truth[cid]
    
    c_steps = c_data['steps']
    t_steps = t_data['steps']
    truth_steps = truth_data['steps']
    
    if c_data != t_data:
        diff_note = "DIFFERENCE"
        diffs.append((cid, c_data, t_data, truth_data))
    else:
        diff_note = "IDENTICAL"
        
    print(f"{cid:<8} | {len(c_steps):<16} | {len(t_steps):<14} | {len(truth_steps):<12} | {diff_note}")

print(f"\nTotal cases with differences between candidate and patched sample: {len(diffs)}")
for cid, c_data, t_data, truth_data in diffs:
    print(f"\nDifference in {cid}:")
    print(f"  Candidate ({len(c_data['steps'])} steps):")
    for s in c_data['steps']: print("   ", s)
    print(f"  Patched ({len(t_data['steps'])} steps):")
    for s in t_data['steps']: print("   ", s)
    print(f"  Truth ({len(truth_data['steps'])} steps):")
    for s in truth_data['steps']: print("   ", s)
