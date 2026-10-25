import os, csv

target_resources = {
    'case_01': ['account_001'],
    'case_03': ['analytics_9406'],
    'case_04': ['analytics_901', 'account_004'],
    'case_09': ['account_3960', 'audit_record_4902'],
    'case_18': ['account_5521', 'audit_record_6645'],
    'case_19': ['support_9553'],
    'case_20': ['account_5037', 'audit_record_5569'],
}

reqs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}

for cid, res_list in target_resources.items():
    req = reqs[cid]
    print(f"\n==================== {cid} (User: {req['email']}) ====================")
    for res in res_list:
        print(f"\nResource: {res}")
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
        for fpath in found_in:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                for lno, line in enumerate(fp, 1):
                    if res in line:
                        print(f"    [{os.path.basename(fpath)}:L{lno}] {line.strip()[:140]}")
