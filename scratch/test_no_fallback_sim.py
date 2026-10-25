import re
import csv
import json
import collections

# Load code/main.py
with open("code/main.py", "r", encoding="utf-8") as f:
    code = f.read()

# Remove the fallback:
# if not acc_res and user_id:
#     m_u = re.match(r"user_(\d+)", user_id)
#     if m_u:
#         d = m_u.group(1)
#         acc_res = f"account_{int(d):03d}" if len(d) <= 2 else f"account_{d}"

code_no_fallback = code.replace(
'''        if not acc_res and user_id:
            m_u = re.match(r"user_(\d+)", user_id)
            if m_u:
                d = m_u.group(1)
                acc_res = f"account_{int(d):03d}" if len(d) <= 2 else f"account_{d}"''',
'''        # Do not fabricate ungrounded account ID from naming convention
        pass'''
)

with open("scratch/temp_no_fallback_main.py", "w", encoding="utf-8") as f:
    f.write(code_no_fallback)

print("Wrote scratch/temp_no_fallback_main.py")
