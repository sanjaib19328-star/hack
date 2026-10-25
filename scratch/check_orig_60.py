import csv, json

empty_cids = set(r['case_id'] for r in csv.DictReader(open('scratch/candidate_output.csv', encoding='utf-8')) if r['deletion_status'] != 'NOT_APPLICABLE' and len(json.loads(r['steps_json'])) == 0)

with open('output.csv', 'r', encoding='utf-8') as f:
    orig = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

print(f"Checking {len(empty_cids)} empty cases against original output.csv:")
for cid in list(sorted(empty_cids))[:8]:
    stat, steps = orig.get(cid, ('', []))
    print(f"\n{cid}: stat={stat}, steps count={len(steps)}")
    for s in steps:
        print(f"  [{s['phase']}] sys={s['system_id']} res={s['resource_id']} op={s['operation']} st={s['state']} ev={s['evidence_id']}")
