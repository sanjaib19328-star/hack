import csv
with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['case_id'] in ('case_21', 'case_22', 'case_23', 'case_25', 'case_28', 'case_29', 'case_31', 'case_32'):
            print(f"{r['case_id']}: email={r['email']} req_at={r['requested_at']} rep_at={r['reported_at']} stat={r['reported_status']}")
