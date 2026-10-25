import os, json, csv

target_resources = {
    'case_01': ['account_001'],
    'case_03': ['analytics_9406'],
    'case_04': ['analytics_901', 'account_004'],
    'case_09': ['account_3960', 'audit_record_4902'],
    'case_18': ['account_5521', 'audit_record_6645'],
    'case_19': ['support_9553'],
    'case_20': ['account_5037', 'audit_record_5569'],
    'case_21': ['analytics_5335', 'account_6440'],
    'case_22': ['account_4990'],
    'case_23': ['export_7364', 'account_410'],
    'case_25': ['account_3136', 'analytics_1895'],
    'case_26': ['analytics_4566', 'account_5684'],
    'case_27': ['analytics_4574', 'account_3866'],
    'case_28': ['account_5482', 'analytics_6077'],
    'case_29': ['account_7012'],
    'case_31': ['account_4857'],
    'case_32': ['account_8858'],
}

reqs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}

# Load evidence manifest
manifest = {}
if os.path.exists('dataset/evidence_manifest.csv'):
    with open('dataset/evidence_manifest.csv', 'r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            manifest[r['evidence_id']] = r

print("Running forensic investigation across evidence...")

for cid, res_list in target_resources.items():
    req = reqs[cid]
    print(f"\n==================== {cid} (User: {req['email']}) ====================")
    for res in res_list:
        print(f"\nResource: {res}")
        # Search across all files in dataset
        found_in = []
        for root, dirs, files in os.walk("dataset"):
            for f in files:
                if f in ("sample_output.csv", "sample_deletion_requests.csv"): continue
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                        if res in content:
                            found_in.append(fpath)
                except Exception:
                    pass
        print(f"  Found in {len(found_in)} files: {found_in}")
        # For each file, print matching lines
        for fpath in found_in:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                for lno, line in enumerate(fp, 1):
                    if res in line:
                        print(f"    [{os.path.basename(fpath)}:L{lno}] {line.strip()[:140]}")
