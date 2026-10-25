import csv, json

truth = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
pred = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('scratch/sample_pred.csv', encoding='utf-8'))}
reqs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}

for cid in ['case_01', 'case_03', 'case_04', 'case_09', 'case_18', 'case_19', 'case_20', 'case_21', 'case_22', 'case_23', 'case_25', 'case_26']:
    req = reqs[cid]
    t_steps = truth[cid]
    p_steps = pred[cid]
    print(f"\n=== {cid} === email={req['email']} req_at={req['requested_at']}")
    print(f"Truth ({len(t_steps)}):")
    for s in t_steps:
        print(f"  T: {s['phase']}:{s['system_id']}:{s['resource_id']}:{s['operation']}:{s['state']}:{s['evidence_id']}")
    print(f"Pred  ({len(p_steps)}):")
    for s in p_steps:
        print(f"  P: {s['phase']}:{s['system_id']}:{s['resource_id']}:{s['operation']}:{s['state']}:{s['evidence_id']}")
