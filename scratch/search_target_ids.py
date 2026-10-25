import os, re

target_ids = [
    "account_3960", "audit_record_4902",
    "account_1919", "audit_record_9683",
    "account_5037", "audit_record_5569",
    "account_4990",
    "account_3136", "analytics_1895",
    "account_5482", "analytics_6077",
    "account_7012",
    "account_4857",
    "account_8858",
    "support_9553", "export_7364", "analytics_9406", "analytics_4574", "analytics_4566"
]

print(f"Searching for {len(target_ids)} target IDs across dataset...")

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
        except Exception as e:
            pass

for tid, matches in results.items():
    print(f"\n--- {tid} --- ({len(matches)} matches)")
    for fpath, lno, snippet in matches[:10]:
        print(f"  {fpath}:{lno} -> {snippet}")
