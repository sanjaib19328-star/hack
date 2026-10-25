import csv
import json
import os
import re
from collections import defaultdict, Counter

print("Starting deep audit of scratch/candidate_output.csv...")

# 1. Load input deletion requests
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    input_requests = {r["case_id"]: r for r in csv.DictReader(f)}

print(f"Total input requests: {len(input_requests)}")

# 2. Load evidence manifest
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    valid_evidence_ids = {r["file_id"] for r in csv.DictReader(f)}

print(f"Total valid evidence IDs in manifest: {len(valid_evidence_ids)}")

# 3. Read candidate output
with open("scratch/candidate_output.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    candidate_rows = list(reader)

print(f"Total candidate rows: {len(candidate_rows)}")

errors = []
warnings = []

# Check row count and headers
if len(candidate_rows) != 518:
    errors.append(f"Expected 518 rows, found {len(candidate_rows)}")

candidate_cids = [r["case_id"] for r in candidate_rows]
if len(set(candidate_cids)) != len(candidate_cids):
    errors.append(f"Duplicate case_ids detected! {len(candidate_cids) - len(set(candidate_cids))} duplicates.")

if set(candidate_cids) != set(input_requests.keys()):
    diff = set(input_requests.keys()) ^ set(candidate_cids)
    errors.append(f"Mismatch between input requests and candidate case IDs: {diff}")

VALID_STATUSES = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
VALID_PHASES = {"FINDING", "REMEDIATION", "VERIFICATION"}
VALID_SYSTEMS = {
    "account_service", "search_service", "analytics_platform",
    "support_platform", "integration_service", "backup_service",
    "security_service", "identity_service", "export_service"
}
PHASE_ORDER = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}

status_counts = Counter()
empty_step_cases = []
not_applicable_cases = []
suspicious_cases = []
invalid_evidence_id_cases = []
step_order_violations = []
step_numbering_violations = []

for idx, r in enumerate(candidate_rows, 1):
    cid = r["case_id"]
    status = r["deletion_status"]
    raw_steps = r["steps_json"]
    
    status_counts[status] += 1
    
    if status not in VALID_STATUSES:
        errors.append(f"Case {cid}: invalid status '{status}'")
        
    try:
        steps = json.loads(raw_steps)
    except Exception as e:
        errors.append(f"Case {cid}: malformed JSON: {e}")
        continue
        
    if not isinstance(steps, list):
        errors.append(f"Case {cid}: steps_json is not an array")
        continue
        
    # Check empty steps
    if len(steps) == 0:
        empty_step_cases.append(cid)
        if status != "NOT_APPLICABLE":
            errors.append(f"Case {cid}: status is {status} but steps array is empty!")
            
    if status == "NOT_APPLICABLE":
        not_applicable_cases.append(cid)
        if len(steps) > 0:
            errors.append(f"Case {cid}: NOT_APPLICABLE must have empty steps [], but has {len(steps)} steps")
            
    # Check phases and step numbering
    seen_step_keys = set()
    prev_phase_rank = 0
    
    for s_idx, s in enumerate(steps, 1):
        # Step numbering consecutive starting at 1
        s_no = s.get("step_no")
        if s_no != s_idx:
            step_numbering_violations.append((cid, s_idx, s_no))
            
        phase = s.get("phase")
        if phase not in VALID_PHASES:
            errors.append(f"Case {cid} step {s_idx}: invalid phase '{phase}'")
            
        phase_rank = PHASE_ORDER.get(phase, 99)
        if phase_rank < prev_phase_rank:
            step_order_violations.append((cid, s_idx, phase, steps[s_idx - 2].get("phase")))
        prev_phase_rank = phase_rank
        
        sys_id = s.get("system_id")
        if sys_id not in VALID_SYSTEMS:
            errors.append(f"Case {cid} step {s_idx}: invalid system_id '{sys_id}'")
            
        # Check evidence ID
        ev_id = s.get("evidence_id")
        if ev_id:
            if ev_id not in valid_evidence_ids:
                invalid_evidence_id_cases.append((cid, s_idx, ev_id))
        else:
            # Empty evidence_id is permitted for REMEDIATION or future VERIFICATION in INCOMPLETE cases
            if status == "COMPLETE":
                errors.append(f"Case {cid} step {s_idx}: COMPLETE status step must not have empty evidence_id!")
            elif phase == "FINDING":
                errors.append(f"Case {cid} step {s_idx}: FINDING step must cite genuine evidence_id!")
                
        # Check duplicate step
        step_key = (phase, sys_id, s.get("resource_id"), s.get("operation"), s.get("state"))
        if step_key in seen_step_keys:
            warnings.append(f"Case {cid}: duplicate step {step_key}")
        seen_step_keys.add(step_key)

print(f"\nStatus distribution across 518 cases:")
for st, cnt in status_counts.items():
    print(f"  - {st}: {cnt} cases ({cnt/len(candidate_rows)*100:.1f}%)")

print(f"\nEmpty steps count: {len(empty_step_cases)}")
print(f"NOT_APPLICABLE cases: {len(not_applicable_cases)} -> {not_applicable_cases}")

# Inspect NOT_APPLICABLE request texts
print(f"\nInspecting NOT_APPLICABLE request texts:")
for cid in not_applicable_cases:
    req = input_requests.get(cid, {})
    txt = req.get("request_text", "")
    print(f"  {cid}: \"{txt[:85]}...\"")

# Check for step numbering / order / evidence errors
if step_numbering_violations:
    errors.append(f"Found {len(step_numbering_violations)} step numbering violations!")
if step_order_violations:
    errors.append(f"Found {len(step_order_violations)} phase ordering violations!")
if invalid_evidence_id_cases:
    errors.append(f"Found {len(invalid_evidence_id_cases)} invalid evidence_id citations!")

print(f"\nAudit Error Count: {len(errors)}")
for err in errors[:20]:
    print(f"  ERROR: {err}")

print(f"Audit Warning Count: {len(warnings)}")
for w in warnings[:10]:
    print(f"  WARNING: {w}")

if not errors:
    print("\nSUCCESS: All 518 cases passed deep structural and semantic integrity verification!")
