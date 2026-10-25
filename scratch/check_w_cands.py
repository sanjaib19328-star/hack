import csv

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    reqs = {r['case_id']: r for r in csv.DictReader(f)}
with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    acts = list(csv.DictReader(f))

for cid in ['case_09', 'case_18', 'case_20', 'case_22', 'case_23', 'case_25', 'case_28', 'case_29', 'case_31', 'case_32']:
    req = reqs[cid]
    cands = [a for a in acts if a['source_system'] == 'deletion_worker' and a['target_system'] == 'account_service' and req['requested_at'] <= a['event_time'] <= req['reported_at']]
    print(cid, req['requested_at'], 'to', req['reported_at'], f'({len(cands)} cands):')
    for a in cands:
        print('  ', a['event_time'], a['activity_id'], a['reported_result'], a['resource_id'])
