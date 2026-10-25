import json
import csv

def load(path):
    d = {}
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            d[r['case_id']] = {
                'status': r['deletion_status'],
                'steps': json.loads(r['steps_json'])
            }
    return d

preds = load('scratch/candidate_sample_pred.csv')
prev = load('scratch/clean_sample_pred.csv')
truth = load('dataset/sample_output.csv')

with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    sample_requests = {r['case_id']: r for r in csv.DictReader(f)}

ambiguous_cases = ['case_09', 'case_18', 'case_20', 'case_22', 'case_23', 'case_25', 'case_28', 'case_29', 'case_31', 'case_32']

print(f"{'Case ID':<8} | {'Email':<25} | {'Latest Steps':<12} | {'Findings':<25} | {'Verifications Retained':<30}")
print("-" * 110)

details = []

for cid in ambiguous_cases:
    req = sample_requests[cid]
    l_steps = preds[cid]['steps']
    p_steps = prev[cid]['steps']
    t_steps = truth[cid]['steps']
    
    findings = [s for s in l_steps if s['phase'] == 'FINDING']
    rems = [s for s in l_steps if s['phase'] == 'REMEDIATION']
    verifs = [s for s in l_steps if s['phase'] == 'VERIFICATION']
    
    # What was removed
    removed = [s for s in p_steps if not any(s['system_id'] == x['system_id'] and s['resource_id'] == x['resource_id'] and s['phase'] == x['phase'] for x in l_steps)]
    
    f_systems = [f"{s['system_id']}:{s['resource_id']}" for s in findings]
    v_systems = [f"{s['system_id']}:{s['resource_id']}" for s in verifs]
    
    print(f"{cid:<8} | {req['email']:<25} | {len(l_steps):<12} | {', '.join(f_systems) or 'None':<25} | {', '.join(v_systems):<30}")
    
    details.append({
        'case_id': cid,
        'email': req['email'],
        'status': preds[cid]['status'],
        'findings': findings,
        'remediations': rems,
        'verifications': verifs,
        'removed': removed,
        'truth_account_step': next((s for s in t_steps if s['system_id'] == 'account_service'), None)
    })

print("\nDetailed Analysis of Removed Steps and Grounding State:")
for d in details:
    cid = d['case_id']
    rem_str = ", ".join(f"{s['system_id']}:{s['resource_id']}" for s in d['removed'])
    t_acc = d['truth_account_step']
    t_acc_str = f"{t_acc['resource_id']} (ev={t_acc.get('evidence_id')})" if t_acc else "None"
    print(f"\n{cid} ({d['email']}):")
    print(f"  Removed by grounding patch: {rem_str}")
    print(f"  Truth account step:         {t_acc_str}")
    print(f"  Retained findings:          {len(d['findings'])}")
    print(f"  Retained verifications:     {len(d['verifications'])}")
