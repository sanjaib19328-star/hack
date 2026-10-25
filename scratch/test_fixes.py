# We will monkey-patch the 3 methods in engine and run audit on sample requests
import importlib.util, csv, json

spec = importlib.util.spec_from_file_location("engine", "code/main.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

# Let's inspect what happens with monkey patching
orig_parse_service_export = engine.DeletionAuditor._parse_service_resource_export
orig_parse_log = engine.DeletionAuditor._parse_log_file
orig_parse_snapshot = engine.DeletionAuditor._parse_snapshot_bundle

def patched_parse_service_export(self, data, file_id, user_id, user_emails, user_phones, user_names, case_row, acc_res, audit_rec):
    findings, remediations, verifications = orig_parse_service_export(self, data, file_id, user_id, user_emails, user_phones, user_names, case_row, acc_res, audit_rec)
    
    # Check export_service with owner_email
    exports = data.get("service_exports", {})
    exp = exports.get("export_service", {})
    for item in exp.get("exports", []):
        res_id = item.get("resource_id")
        c_email = item.get("owner_email") or item.get("customer_email")
        c_ref = item.get("customer_reference")
        matches = (c_email and str(c_email).lower() in user_emails) or (c_ref and str(c_ref) == user_id)
        if matches:
            # Check if already added
            if not any(f.get("resource_id") == res_id for f in findings):
                findings.append({"phase": "FINDING", "system_id": "export_service", "resource_id": res_id, "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": file_id})
                remediations.append({"phase": "REMEDIATION", "system_id": "export_service", "resource_id": res_id, "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": ""})
                verifications.append({"phase": "VERIFICATION", "system_id": "export_service", "resource_id": res_id, "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""})
    return findings, remediations, verifications

def patched_parse_snapshot_bundle(self, data, file_id, user_id, user_emails, user_phones, user_names, case_row, acc_res, audit_rec):
    # Call original but don't add false verifications when store is empty or unlinked
    findings = []
    remediations = []
    verifications = []

    for s in data.get("snapshots", []):
        store = s.get("data_store")
        records = s.get("records", [])

        if store == "identity_service":
            for r in records:
                res_id = r.get("resource_id")
                c_ref = r.get("customer_reference") or r.get("subject_reference") or r.get("user_id")
                if c_ref == user_id or any(e in str(r).lower() for e in user_emails):
                    has_pii = bool(r.get("email") or r.get("phone") or r.get("name") or r.get("full_name") or r.get("email_hash"))
                    if has_pii:
                        findings.append({"phase": "FINDING", "system_id": "identity_service", "resource_id": res_id, "operation": "REPORT_EXPOSED_PII", "state": "PRESENT", "evidence_id": file_id})
                        remediations.append({"phase": "REMEDIATION", "system_id": "identity_service", "resource_id": res_id, "operation": "REDACT_RECORD", "state": "REDACTED", "evidence_id": ""})
                        verifications.append({"phase": "VERIFICATION", "system_id": "identity_service", "resource_id": res_id, "operation": "VERIFY_RECORD_REDACTED", "state": "REDACTED", "evidence_id": ""})
                    else:
                        verifications.append({"phase": "VERIFICATION", "system_id": "identity_service", "resource_id": res_id, "operation": "VERIFY_RECORD_REDACTED", "state": "REDACTED", "evidence_id": file_id})

        elif store == "account_service":
            for r in records:
                res_id = r.get("resource_id")
                c_ref = r.get("customer_reference") or r.get("user_id")
                e = (r.get("email") or "").lower()
                if c_ref == user_id or e in user_emails or res_id == acc_res:
                    findings.append({"phase": "FINDING", "system_id": "account_service", "resource_id": res_id, "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": file_id})
                    remediations.append({"phase": "REMEDIATION", "system_id": "account_service", "resource_id": res_id, "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": ""})
                    verifications.append({"phase": "VERIFICATION", "system_id": "account_service", "resource_id": res_id, "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""})

        elif store == "security_service":
            for r in records:
                res_id = r.get("resource_id")
                sub_ref = r.get("subject_reference")
                if sub_ref == user_id or res_id == audit_rec:
                    verifications.append({"phase": "VERIFICATION", "system_id": "security_service", "resource_id": res_id, "operation": "VERIFY_RECORD_PRESENT", "state": "PRESENT", "evidence_id": file_id})

        elif store == "analytics_platform":
            for r in records:
                res_id = r.get("resource_id")
                c_ref = r.get("customer_reference") or r.get("user_id")
                e = (r.get("email") or "").lower()
                if c_ref == user_id or e in user_emails:
                    has_pii = bool(r.get("email") or r.get("phone") or r.get("email_hash"))
                    if has_pii:
                        findings.append({"phase": "FINDING", "system_id": "analytics_platform", "resource_id": res_id, "operation": "REPORT_EXPOSED_PII", "state": "PRESENT", "evidence_id": file_id})
                        remediations.append({"phase": "REMEDIATION", "system_id": "analytics_platform", "resource_id": res_id, "operation": "ANONYMIZE_RECORD", "state": "ANONYMIZED", "evidence_id": ""})
                        verifications.append({"phase": "VERIFICATION", "system_id": "analytics_platform", "resource_id": res_id, "operation": "VERIFY_RECORD_ANONYMIZED", "state": "ANONYMIZED", "evidence_id": ""})
                    else:
                        verifications.append({"phase": "VERIFICATION", "system_id": "analytics_platform", "resource_id": res_id, "operation": "VERIFY_RECORD_ANONYMIZED", "state": "ANONYMIZED", "evidence_id": file_id})

        elif store == "export_service":
            for r in records:
                res_id = r.get("resource_id")
                e = (r.get("owner_email") or r.get("customer_email") or "").lower()
                c_ref = r.get("customer_reference") or r.get("user_id")
                if e in user_emails or c_ref == user_id:
                    dl = r.get("download_available", False)
                    if dl:
                        findings.append({"phase": "FINDING", "system_id": "export_service", "resource_id": res_id, "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": file_id})
                        remediations.append({"phase": "REMEDIATION", "system_id": "export_service", "resource_id": res_id, "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": ""})
                        verifications.append({"phase": "VERIFICATION", "system_id": "export_service", "resource_id": res_id, "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""})
                    else:
                        verifications.append({"phase": "VERIFICATION", "system_id": "export_service", "resource_id": res_id, "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": file_id})

    return findings, remediations, verifications

def patched_parse_log(self, file_path, file_id, origin, user_id, user_emails, user_phones, user_names, user_email_hashes, case_row, acc_res, audit_rec):
    import re
    findings = []
    remediations = []
    verifications = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return findings, remediations, verifications

    trace_to_user = {}
    for line in lines:
        line_str = line.strip()
        m_tr = re.search(r"trace_id=([^\s]+)", line_str)
        if m_tr:
            tr = m_tr.group(1)
            user_in_line = (user_id and user_id in line_str) or any(e in line_str.lower() for e in user_emails) or any(eh in line_str for eh in user_email_hashes)
            if user_in_line:
                trace_to_user[tr] = user_id

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        m_tr = re.search(r"trace_id=([^\s]+)", line_str)
        tr = m_tr.group(1) if m_tr else None

        user_mentioned = (user_id and user_id in line_str) or any(e in line_str.lower() for e in user_emails) or (tr and tr in trace_to_user) or any(eh in line_str for eh in user_email_hashes)
        if not user_mentioned:
            continue

        m_res = re.search(r'resource_id="?(\w+)"?', line_str)
        m_svc = re.search(r'(?:service|system)="?(\w+)"?', line_str)
        res_id = m_res.group(1) if m_res else None
        svc = m_svc.group(1) if m_svc else None

        if not res_id:
            continue

        if svc in {"support_platform", "support_replica", "customer_support"}:
            if "marker_found=false" in line_str or ("contact_query_completed" in line_str and "rows=1" in line_str):
                findings.append({"phase": "FINDING", "system_id": "support_platform", "resource_id": res_id, "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": file_id})
                remediations.append({"phase": "REMEDIATION", "system_id": "support_platform", "resource_id": res_id, "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": ""})
                verifications.append({"phase": "VERIFICATION", "system_id": "support_platform", "resource_id": res_id, "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""})
            else:
                has_pii = ("message_pii_scan" in line_str) or bool(re.search(r"requester_email=[^\s,]+", line_str) and "requester_email=null" not in line_str) or bool(re.search(r"matched_value=\"?[^\s\",]+\"?", line_str) and "matched_value=\"\"" not in line_str and "matched_value=null" not in line_str)
                if has_pii:
                    findings.append({"phase": "FINDING", "system_id": "support_platform", "resource_id": res_id, "operation": "REPORT_EXPOSED_PII", "state": "PRESENT", "evidence_id": file_id})
                    remediations.append({"phase": "REMEDIATION", "system_id": "support_platform", "resource_id": res_id, "operation": "REDACT_RECORD", "state": "REDACTED", "evidence_id": ""})
                    verifications.append({"phase": "VERIFICATION", "system_id": "support_platform", "resource_id": res_id, "operation": "VERIFY_RECORD_REDACTED", "state": "REDACTED", "evidence_id": ""})
                else:
                    verifications.append({"phase": "VERIFICATION", "system_id": "support_platform", "resource_id": res_id, "operation": "VERIFY_RECORD_REDACTED", "state": "REDACTED", "evidence_id": file_id})

    # Call orig for remaining services
    f_orig, r_orig, v_orig = orig_parse_log(self, file_path, file_id, origin, user_id, user_emails, user_phones, user_names, user_email_hashes, case_row, acc_res, audit_rec)
    for s in f_orig:
        if s.get("system_id") != "support_platform":
            findings.append(s)
    for s in r_orig:
        if s.get("system_id") != "support_platform":
            remediations.append(s)
    for s in v_orig:
        if s.get("system_id") != "support_platform":
            verifications.append(s)

    return findings, remediations, verifications

engine.DeletionAuditor._parse_service_resource_export = patched_parse_service_export
engine.DeletionAuditor._parse_snapshot_bundle = patched_parse_snapshot_bundle
engine.DeletionAuditor._parse_log_file = patched_parse_log

# Run audit on sample requests and evaluate
engine.run_audit("dataset/sample_deletion_requests.csv", "scratch/test_patched_pred.csv", "dataset")

# Compare with sample_output.csv
from code.evaluation.main import evaluate_predictions
metrics = evaluate_predictions("scratch/test_patched_pred.csv", "dataset/sample_output.csv")
print("Status Accuracy:", f"{metrics['status_accuracy']*100:.2f}% ({metrics['status_matches']}/{metrics['total_cases']})")
print("Exact Sequence Accuracy:", f"{metrics['sequence_accuracy']*100:.2f}% ({metrics['sequence_matches']}/{metrics['total_cases']})")
print("Field-Level Accuracy:", f"{metrics['field_accuracy']*100:.2f}% ({metrics['field_matches']}/{metrics['total_fields']})")
print("Total Mismatches:", len(metrics['mismatches']))
for m in metrics['mismatches'][:5]:
    print("  ", m)
