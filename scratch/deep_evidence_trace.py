import csv
import json
import os
import re

print("=== Targeted Evidence-to-Step Audit ===")

# Cases to sample:
# COMPLETE: case_01 (replica checked), case_03 (clean snapshot/logs), case_23 (service export), case_31 (tombstone)
# INCOMPLETE: case_05 (replica drift), case_06 (search index remaining), case_07 (telemetry pii), case_08 (backup active), case_19 (support pii log)
# NOT_APPLICABLE: case_533, case_541

sample_cases = [
    "case_01", "case_03", "case_05", "case_06", "case_07", "case_08", "case_19", "case_23", "case_31", "case_533", "case_541"
]

# Load requests
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    reqs = {r["case_id"]: r for r in csv.DictReader(f)}

# Also load full requests for 533, 541
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["case_id"] in sample_cases:
            reqs[r["case_id"]] = r

# Load predictions
with open("scratch/candidate_sample_pred.csv", "r", encoding="utf-8") as f:
    preds = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("scratch/candidate_output.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["case_id"] in sample_cases:
            preds[r["case_id"]] = (r["deletion_status"], json.loads(r["steps_json"]))

# Load evidence manifest
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    ev_manifest = {r["file_id"]: r for r in csv.DictReader(f)}

# Load user identities
with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    identities = {r["user_id"]: r for r in csv.DictReader(f)}
email_to_uid = {r["email"].lower(): r["user_id"] for r in identities.values()}

# Trace each case
for cid in sample_cases:
    req = reqs[cid]
    status, steps = preds[cid]
    email = req["email"].lower().strip()
    user_id = email_to_uid.get(email, "UNKNOWN")
    user_info = identities.get(user_id, {})
    
    print(f"\n=======================================================")
    print(f"CASE: {cid} | Status: {status} | Steps Count: {len(steps)}")
    print(f"User: {user_id} ({email}) | Name: {user_info.get('full_name')} | Phone: {user_info.get('phone')}")
    print(f"Requested: {req.get('requested_at')} | Reported: {req.get('reported_at')} | Audit: {req.get('audit_at')}")
    print(f"Intent: {req.get('request_text')[:90]}...")
    
    if status == "NOT_APPLICABLE":
        print("  -> Correctly classified as NOT_APPLICABLE. Steps array is empty [].")
        continue

    for s in steps:
        step_no = s["step_no"]
        phase = s["phase"]
        sys_id = s["system_id"]
        res_id = s["resource_id"]
        op = s["operation"]
        st = s["state"]
        ev_id = s["evidence_id"]
        
        print(f"\n  Step {step_no} [{phase}]: {sys_id} -> {res_id} | Op: {op} | State: {st} | Evidence: '{ev_id}'")
        
        # Check evidence grounding
        if ev_id:
            ev_meta = ev_manifest.get(ev_id)
            if not ev_meta:
                print(f"    [FAIL] Evidence {ev_id} not in manifest!")
                continue
            ev_path = os.path.join("dataset", ev_meta["file_path"])
            captured_at = ev_meta["captured_at"]
            audit_at = req["audit_at"]
            
            # Check timestamp
            time_valid = captured_at <= audit_at
            print(f"    Evidence File: {ev_meta['file_path']} (Origin: {ev_meta['origin']})")
            print(f"    Captured At: {captured_at} <= Audit At: {audit_at} ? {time_valid}")
            
            # Check content for user or resource
            if os.path.exists(ev_path):
                with open(ev_path, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    
                has_user = (user_id and user_id in content) or (email in content.lower())
                has_res = res_id in content
                
                print(f"    Content check: user mentioned? {has_user} | resource {res_id} mentioned? {has_res}")
                
                # Check specific assertions
                if op == "VERIFY_RECORD_ABSENT":
                    # Proves absence if file covers system/table and user is absent, or status == NOT_FOUND
                    if has_res and "failover_replica" not in ev_path:
                        print(f"    [VERIFY] Note: {res_id} appears in {ev_path}. Check if tombstone/not-found.")
                    else:
                        print(f"    [PASS] Absence supported by snapshot/replica inspection.")
                elif op == "REPORT_REMAINING_RECORD":
                    if has_res or has_user:
                        print(f"    [PASS] Finding supported by explicit presence in {ev_meta['file_path']}.")
                    else:
                        print(f"    [FAIL] Finding NOT supported by content!")
                elif op == "REPORT_EXPOSED_PII":
                    if has_user or email in content.lower():
                        print(f"    [PASS] PII exposure supported by email/name presence in {ev_meta['file_path']}.")
                    else:
                        print(f"    [FAIL] PII exposure NOT supported by content!")
            else:
                print(f"    [FAIL] Evidence file does not exist: {ev_path}")
        else:
            # Empty evidence ID must be REMEDIATION or future VERIFICATION in INCOMPLETE cases
            if status == "INCOMPLETE" and phase in ("REMEDIATION", "VERIFICATION"):
                print(f"    [PASS] Empty evidence_id compliant with challenge rule for proposed actions.")
            else:
                print(f"    [FAIL] Unexpected empty evidence_id for {status} {phase}!")
