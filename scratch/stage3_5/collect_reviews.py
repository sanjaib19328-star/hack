import json
import csv
import os

from compare_stages import load

preds = load('scratch/candidate_sample_pred.csv')
sample_requests = {}
with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        sample_requests[r['case_id']] = r

review_cases = [
    # 14 changed cases
    'case_06', 'case_07', 'case_08', 'case_09', 'case_10',
    'case_18', 'case_20', 'case_22', 'case_23', 'case_25',
    'case_28', 'case_29', 'case_31', 'case_32',
    # 6 unchanged cases representing distinct patterns
    'case_01', 'case_05', 'case_11', 'case_13', 'case_19', 'case_24'
]

print(f"Total cases to review: {len(review_cases)}")

case_reviews = []

for cid in review_cases:
    req = sample_requests[cid]
    p_data = preds[cid]
    status = p_data['status']
    steps = p_data['steps']
    
    findings = [s for s in steps if s['phase'] == 'FINDING']
    remediations = [s for s in steps if s['phase'] == 'REMEDIATION']
    verifications = [s for s in steps if s['phase'] == 'VERIFICATION']
    
    review = {
        'case_id': cid,
        'email': req['email'],
        'reported_status': req['reported_status'],
        'audit_status': status,
        'step_count': len(steps),
        'findings': findings,
        'remediations': remediations,
        'verifications': verifications,
    }
    case_reviews.append(review)

with open('scratch/stage3_5/case_reviews_raw.json', 'w', encoding='utf-8') as f:
    json.dump(case_reviews, f, indent=2)

print("Saved raw reviews to scratch/stage3_5/case_reviews_raw.json")
