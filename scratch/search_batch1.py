import os

target_ids = [
    "account_3960", "audit_record_4902",
    "account_1919", "audit_record_9683",
    "account_5037", "audit_record_5569"
]

results = {tid: [] for tid in target_ids}
for root, dirs, files in os.walk("dataset"):
    for f in files:
        fpath = os.path.join(root, f)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                for line_no, line in enumerate(fp, 1):
                    for tid in target_ids:
                        if tid in line:
                            results[tid].append((fpath, line_no, line.strip()[:160]))
        except Exception:
            pass

for tid, matches in results.items():
    print(f"\n--- {tid} --- ({len(matches)} matches)")
    for fpath, lno, snippet in matches:
        print(f"  {fpath}:{lno} -> {snippet}")
