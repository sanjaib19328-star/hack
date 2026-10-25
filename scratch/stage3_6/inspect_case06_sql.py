import csv
import json
import os

with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    case06_req = next(r for r in csv.DictReader(f) if r['case_id'] == 'case_06')

print("case_06 Request:")
for k, v in case06_req.items():
    print(f"  {k}: {v}")

with open('dataset/evidence_files.csv', encoding='utf-8') as f:
    ev_files = list(csv.DictReader(f))

# Window for case_06:
# requested_at = '2026-08-29T06:51:00Z', audit_at = '2026-09-10T09:15:00Z'
window_evs = [
    e for e in ev_files 
    if case06_req['requested_at'] <= e['captured_at'] <= case06_req['audit_at']
]

print(f"\nEvidence files in window ({len(window_evs)}):")
for e in window_evs:
    print(f"  {e['file_id']}: {e['file_path']} (captured_at={e['captured_at']}, origin={e['origin']})")

# Look specifically for customer_search_primary_20260910.sql
for e in ev_files:
    if 'customer_search_primary_20260910.sql' in e['file_path']:
        print(f"\ncustomer_search_primary_20260910.sql entry:")
        print(f"  file_id: {e['file_id']}, captured_at: {e['captured_at']}, origin: {e['origin']}")
        
# Inspect table DDL and records in customer_search_primary_20260910.sql
sql_path = 'dataset/evidence/databases/customer_search_primary_20260910.sql'
print(f"\nReading {sql_path}:")
with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for line in lines[:30]:
    if 'CREATE TABLE' in line or 'INSERT' in line or 'search_documents' in line:
        print("  ", line.strip())

print("\nLines mentioning jonas.berg or account_006 or search_001:")
for line in lines:
    if any(k in line for k in ['jonas.berg', 'account_006', 'search_001']):
        print("  ", line.strip())
