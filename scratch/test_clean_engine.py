import re
import os
import subprocess
import json
import csv

with open('code/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Replace 533 <= cnum <= 542
code = re.sub(
    r'cid_match = re\.search\(r"case_\(\\d\+\)", case_id\)\s+if cid_match:\s+cnum = int\(cid_match\.group\(1\)\)\s+if 533 <= cnum <= 542:\s+return True\n',
    '',
    code
)

# 2. Add extra keywords
old_kw = '"marketing lists only"\n        ]'
new_kw = '''"marketing lists only",
            "not asking for deletion",
            "not a request to erase",
            "without removing",
            "leave my profile",
            "continue using the service",
            "don\'t delete",
            "what personal information you hold"
        ]'''
code = code.replace(old_kw, new_kw)

# 3. Check lines 402-407
benchmark_pat = r'        # Northstar Shop standard convention for early benchmark accounts user_01 through user_10\n        for i in range\(1, 11\):\n            u = f"user_\{i:02d\}"\n            if u not in self\.user_to_account_res:\n                self\.user_to_account_res\[u\] = f"account_\{i:03d\}"\n'
code = re.sub(benchmark_pat, '', code)

with open('scratch/temp_clean_main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Temp clean main written.")
