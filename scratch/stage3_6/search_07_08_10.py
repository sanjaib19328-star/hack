import os
import csv
import json

targets = {
    'case_07': ['priya.raman@gmail.com', 'user_007', '+91 98765 73142', 'priya raman', 'account_007'],
    'case_08': ['gabriel.costa@proton.me', 'user_008', 'gabriel costa', 'account_008'],
    'case_10': ['nadia.ionescu@yahoo.com', 'user_010', 'nadia ionescu', 'account_010']
}

print("=" * 80)
print("DEEP SEARCH ACROSS ENTIRE DATASET FOR CASES 07, 08, 10")
print("=" * 80)

results = {k: [] for k in targets}

for root, dirs, files in os.walk('dataset'):
    for f in sorted(files):
        if f == 'sample_output.csv':
            continue
        path = os.path.join(root, f)
        rel_path = os.path.relpath(path, 'dataset')
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as fl:
                content = fl.read().lower()
                for cid, terms in targets.items():
                    for t in terms:
                        if t.lower() in content:
                            results[cid].append((rel_path, t))
        except Exception as e:
            pass

for cid, matches in results.items():
    print(f"\n--- {cid} MATCHES ---")
    matched_files = set(m[0] for m in matches)
    for f in sorted(matched_files):
        terms_in_f = set(m[1] for m in matches if m[0] == f)
        print(f"  File: {f} | Matched terms: {terms_in_f}")
