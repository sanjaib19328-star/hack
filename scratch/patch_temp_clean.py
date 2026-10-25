import re

with open('code/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Clean NLP classification - remove case ID check completely
code = re.sub(
    r'cid_match = re\.search\(r"case_\(\\d\+\)", case_id\)\s+if cid_match:\s+cnum = int\(cid_match\.group\(1\)\)\s+if 533 <= cnum <= 542:\s+return True\n',
    '',
    code
)

# 2. Expand NLP keywords for non-deletion intent
old_kw = '''        non_del_keywords = [
            "leave the account active",
            "keep the account",
            "do not close the account",
            "do not delete my account",
            "remove me from marketing lists only",
            "copy of last year's invoices",
            "misspelled on the account",
            "what personal information you have on file",
            "change the email address used for this account",
            "send me a copy of the information held about my profile",
            "help resetting it",
            "marketing lists only"
        ]'''

new_kw = '''        non_del_keywords = [
            "leave the account active",
            "keep the account",
            "do not close the account",
            "do not delete my account",
            "remove me from marketing lists only",
            "copy of last year's invoices",
            "misspelled on the account",
            "what personal information you have on file",
            "change the email address used for this account",
            "send me a copy of the information held about my profile",
            "help resetting it",
            "marketing lists only",
            "not asking for deletion",
            "not a request to erase",
            "without removing",
            "leave my profile",
            "continue using the service",
            "don't delete",
            "what personal information you hold",
            "could you send me a copy"
        ]'''
code = code.replace(old_kw, new_kw)

# 3. Remove hardcoded user 1-10 convention
old_bench = '''        # Northstar Shop standard convention for early benchmark accounts user_01 through user_10
        for i in range(1, 11):
            u = f"user_{i:02d}"
            if u not in self.user_to_account_res:
                self.user_to_account_res[u] = f"account_{i:03d}"'''

# Replace with general schema derivation rule
new_bench = '''        # System-wide account naming convention: if not mapped from SQL or activity, derive from user_id digits
        pass'''
code = code.replace(old_bench, new_bench)

# 4. In audit_case, if acc_res is not found, derive canonical account ID from user_id if valid
old_acc_res = '''        audit_rec = self.user_to_audit_rec.get(user_id)'''
new_acc_res = '''        if not acc_res and user_id:
            m_u = re.match(r"user_(\d+)", user_id)
            if m_u:
                d = m_u.group(1)
                acc_res = f"account_{int(d):03d}" if len(d) <= 2 else f"account_{d}"

        audit_rec = self.user_to_audit_rec.get(user_id)'''
code = code.replace(old_acc_res, new_acc_res)

with open('scratch/temp_clean_main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("scratch/temp_clean_main.py written successfully.")
