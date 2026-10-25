with open("code/main.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update account resolution to distinguish grounded vs ungrounded
old_acc_block = '''        acc_res = self.user_to_account_res.get(user_id)
        if not acc_res and requested_at:
            rep_at = case_row.get("reported_at") or audit_at
            rep_stat = case_row.get("reported_status")
            w_cands = [
                a for a in self.activity_tracker.activities
                if a.get("source_system") == "deletion_worker" and 
                   a.get("target_system") == "account_service" and 
                   requested_at <= a.get("event_time", "") <= rep_at
            ]
            matched_stat = [
                a for a in w_cands
                if (rep_stat == "COMPLETE" and a.get("reported_result") == "SUCCESS") or
                   (rep_stat == "PARTIALLY_COMPLETE" and a.get("reported_result") in ("PARTIAL", "FAILED"))
            ]
            if len(matched_stat) == 1:
                acc_res = matched_stat[0].get("resource_id")
            elif len(w_cands) == 1:
                acc_res = w_cands[0].get("resource_id")

        if not acc_res and user_id:
            m_u = re.match(r"user_(\d+)", user_id)
            if m_u:
                d = m_u.group(1)
                acc_res = f"account_{int(d):03d}" if len(d) <= 2 else f"account_{d}"

        audit_rec = self.user_to_audit_rec.get(user_id)'''

new_acc_block = '''        acc_res = self.user_to_account_res.get(user_id)
        if not acc_res and requested_at:
            rep_at = case_row.get("reported_at") or audit_at
            rep_stat = case_row.get("reported_status")
            w_cands = [
                a for a in self.activity_tracker.activities
                if a.get("source_system") == "deletion_worker" and 
                   a.get("target_system") == "account_service" and 
                   requested_at <= a.get("event_time", "") <= rep_at
            ]
            matched_stat = [
                a for a in w_cands
                if (rep_stat == "COMPLETE" and a.get("reported_result") == "SUCCESS") or
                   (rep_stat == "PARTIALLY_COMPLETE" and a.get("reported_result") in ("PARTIAL", "FAILED"))
            ]
            if len(matched_stat) == 1:
                acc_res = matched_stat[0].get("resource_id")
            elif len(w_cands) == 1:
                acc_res = w_cands[0].get("resource_id")

        is_grounded_acc = (acc_res is not None)
        fallback_acc = None
        if not acc_res and user_id:
            m_u = re.match(r"user_(\d+)", user_id)
            if m_u:
                d = m_u.group(1)
                fallback_acc = f"account_{int(d):03d}" if len(d) <= 2 else f"account_{d}"

        audit_rec = self.user_to_audit_rec.get(user_id)'''

# 2. Update section 5 Core Account Service Verification
old_sec5 = '''        # 5. Core Account Service Verification
        # In a compliant case, account profile must be confirmed absent
        if acc_res and not any(s.get("system_id") == "account_service" for s in (findings + verifications)):
            verifications.append({
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": acc_res,
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": primary_batch_ev
            })'''

new_sec5 = '''        # 5. Core Account Service Verification
        # Only verify account profile when grounded in evidence/logs, or when no other checks exist to establish absence
        if is_grounded_acc and acc_res and not any(s.get("system_id") == "account_service" for s in (findings + verifications)):
            verifications.append({
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": acc_res,
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": primary_batch_ev
            })
        elif not (findings or verifications) and fallback_acc:
            verifications.append({
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": fallback_acc,
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": primary_batch_ev
            })'''

if old_acc_block in code and old_sec5 in code:
    code = code.replace(old_acc_block, new_acc_block)
    code = code.replace(old_sec5, new_sec5)
    with open("code/main.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("SUCCESS: code/main.py updated with grounded account identity logic.")
else:
    print("FAILED to find code blocks in code/main.py!")
