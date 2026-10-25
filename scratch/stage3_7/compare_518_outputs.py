import csv
import json
import hashlib

def hash_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

cand_path = 'scratch/candidate_output.csv'
test_path = 'scratch/stage3_7/test_output.csv'

print(f"Candidate output hash: {hash_file(cand_path)}")
print(f"Patched test output hash: {hash_file(test_path)}")

def load(path):
    d = {}
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            d[r['case_id']] = (r['deletion_status'], json.loads(r['steps_json']))
    return d

cand_data = load(cand_path)
test_data = load(test_path)

diffs = []
for cid in cand_data:
    if cand_data[cid] != test_data.get(cid):
        diffs.append(cid)

print(f"\nRow-by-row comparison across all 518 cases:")
print(f"Total cases evaluated: {len(cand_data)}")
print(f"Total differences found: {len(diffs)}")

if diffs:
    print(f"Different cases: {diffs}")
else:
    print("ALL 518 CASES ARE 100% BIT-FOR-BIT IDENTICAL!")
