import csv

req_1 = {
    'requested_at': '2026-08-20T14:12:00Z',
    'reported_at': '2026-08-21T09:30:00Z',
    'reported_status': 'COMPLETE',
    'audit_at': '2026-08-25T10:00:00Z'
}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    acts = list(csv.DictReader(f))

w_cands = [
    a for a in acts
    if a.get('source_system') == 'deletion_worker' and
       a.get('target_system') == 'account_service' and
       req_1['requested_at'] <= a.get('event_time', '') <= req_1['reported_at']
]

print(f"w_cands count: {len(w_cands)}")
for a in w_cands:
    print(a['event_time'], a['activity_id'], a['reported_result'], a['resource_id'], a['details'])
