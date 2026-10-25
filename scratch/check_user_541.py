import os
import sys

# Load main directly
import importlib.util
spec = importlib.util.spec_from_file_location("main", "code/main.py")
main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_mod)

auditor = main_mod.DeletionAuditor("dataset")
print("user_541 acc_res:", auditor.user_to_account_res.get("user_541"))
print("user_541 audit_rec:", auditor.user_to_audit_rec.get("user_541"))
print("case_31 user_id:", auditor.resolver.resolve_email("yuki.sato@yahoo.com"))
