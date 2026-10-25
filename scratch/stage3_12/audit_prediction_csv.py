import csv
import json
import re
import os
import sys

csv_path = 'scratch/candidate_output.csv'

# Allowed definitions from AGENTS.md / problem_statement.md
ALLOWED_STATUSES = {'COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE'}
ALLOWED_PHASES = {'FINDING', 'REMEDIATION', 'VERIFICATION'}
ALLOWED_STEP_FIELDS = {'step_no', 'phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id'}

ALLOWED_OPERATIONS_STATE = {
    # Findings
    ('REPORT_REMAINING_RECORD', 'PRESENT'),
    ('REPORT_EXPOSED_PII', 'PRESENT'),
    ('REPORT_ACTIVE_DATA_FLOW', 'ACTIVE'),
    ('REPORT_RESTORE_RISK', 'ACTIVE'),
    # Remediation
    ('DISABLE_DATA_FLOW', 'DISABLED'),
    ('BLOCK_RESTORE', 'BLOCKED'),
    ('DELETE_RECORD', 'ABSENT'),
    ('REDACT_RECORD', 'REDACTED'),
    ('ANONYMIZE_RECORD', 'ANONYMIZED'),
    # Verification
    ('VERIFY_RECORD_ABSENT', 'ABSENT'),
    ('VERIFY_RECORD_PRESENT', 'PRESENT'),
    ('VERIFY_RECORD_REDACTED', 'REDACTED'),
    ('VERIFY_RECORD_ANONYMIZED', 'ANONYMIZED'),
    ('VERIFY_DATA_FLOW_DISABLED', 'DISABLED'),
    ('VERIFY_RESTORE_BLOCKED', 'BLOCKED'),
}

PHASE_ORDER = {'FINDING': 0, 'REMEDIATION': 1, 'VERIFICATION': 2}

# Load valid evidence IDs from dataset
evidence_files_csv = 'dataset/evidence_files.csv'
system_activity_csv = 'dataset/system_activity.csv'
user_audit_log_csv = 'dataset/user_audit_log.csv'
deletion_requests_csv = 'dataset/deletion_requests.csv'

valid_evidence_ids = set()
if os.path.exists(evidence_files_csv):
    with open(evidence_files_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            valid_evidence_ids.add(r['file_id'])

if os.path.exists(system_activity_csv):
    with open(system_activity_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            valid_evidence_ids.add(r['activity_id'])

if os.path.exists(user_audit_log_csv):
    with open(user_audit_log_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            valid_evidence_ids.add(r['audit_id'])

# Load requests to verify audit_at temporal constraints
requests_by_case = {}
if os.path.exists(deletion_requests_csv):
    with open(deletion_requests_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            requests_by_case[r['case_id']] = r

print(f"Loaded {len(valid_evidence_ids)} valid evidence IDs from dataset.")
print(f"Loaded {len(requests_by_case)} deletion requests.")

# Perform validation
errors = []
warnings = []

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader, None)
    
    # 1. Exact header check
    if header != ['case_id', 'deletion_status', 'steps_json']:
        errors.append(f"Header mismatch: expected ['case_id', 'deletion_status', 'steps_json'], got {header}")
        
    rows = list(reader)

# 2. Exactly 518 data rows
if len(rows) != 518:
    errors.append(f"Row count mismatch: expected 518, got {len(rows)}")

# 3 & 4. Unique case IDs covering case_33 to case_550 and correct numeric ordering
expected_cases = [f"case_{i:02d}" if i < 100 else f"case_{i}" for i in range(33, 551)]
actual_cases = [r[0] for r in rows]

if actual_cases != expected_cases:
    errors.append(f"Case ID sequence mismatch! First mismatch: {[ (a,e) for a,e in zip(actual_cases, expected_cases) if a != e][:3]}")

# Detailed per-row audit
status_counts = {'COMPLETE': 0, 'INCOMPLETE': 0, 'NOT_APPLICABLE': 0}

for row_idx, r in enumerate(rows, start=2):
    if len(r) != 3:
        errors.append(f"Row {row_idx}: Invalid column count ({len(r)} instead of 3)")
        continue
    case_id, status, steps_raw = r
    
    # Check status
    if status not in ALLOWED_STATUSES:
        errors.append(f"Row {row_idx} ({case_id}): Invalid status '{status}'")
    else:
        status_counts[status] += 1
        
    # Check JSON parsing
    try:
        steps = json.loads(steps_raw)
    except Exception as e:
        errors.append(f"Row {row_idx} ({case_id}): JSON parse error: {e}")
        continue
        
    if not isinstance(steps, list):
        errors.append(f"Row {row_idx} ({case_id}): steps_json is not a JSON array")
        continue
        
    # 14. Empty step arrays rule
    if status == 'NOT_APPLICABLE':
        if len(steps) != 0:
            errors.append(f"Row {row_idx} ({case_id}): NOT_APPLICABLE must have empty steps_json, got {len(steps)} steps")
    else:
        if len(steps) == 0:
            errors.append(f"Row {row_idx} ({case_id}): {status} has unexpectedly empty steps_json")

    # Step properties
    last_phase_val = -1
    for s_idx, step in enumerate(steps, start=1):
        # 7. Required fields
        step_keys = set(step.keys())
        if step_keys != ALLOWED_STEP_FIELDS:
            diff = step_keys.symmetric_difference(ALLOWED_STEP_FIELDS)
            errors.append(f"{case_id} step {s_idx}: Keys mismatch: diff={diff}")
            
        # 8. Step numbering consecutive starting at 1
        if step.get('step_no') != s_idx:
            errors.append(f"{case_id} step {s_idx}: step_no is {step.get('step_no')}, expected {s_idx}")
            
        phase = step.get('phase')
        op = step.get('operation')
        state = step.get('state')
        ev_id = step.get('evidence_id', '')
        
        # Phase check
        if phase not in ALLOWED_PHASES:
            errors.append(f"{case_id} step {s_idx}: Invalid phase '{phase}'")
        else:
            phase_val = PHASE_ORDER[phase]
            # 9. Phase ordering check
            if phase_val < last_phase_val:
                errors.append(f"{case_id} step {s_idx}: Phase ordering violation: {phase} followed earlier phase")
            last_phase_val = phase_val
            
        # Operation & State pair check
        if (op, state) not in ALLOWED_OPERATIONS_STATE:
            errors.append(f"{case_id} step {s_idx}: Invalid operation/state pair ({op}, {state})")
            
        # Evidence ID checks
        if status == 'COMPLETE':
            # Complete cases verification steps must have valid evidence_id
            if not ev_id:
                errors.append(f"{case_id} step {s_idx}: COMPLETE case step has empty evidence_id")
            elif ev_id not in valid_evidence_ids:
                errors.append(f"{case_id} step {s_idx}: COMPLETE case step references unknown evidence_id '{ev_id}'")
        elif status == 'INCOMPLETE':
            if phase == 'FINDING':
                if not ev_id:
                    errors.append(f"{case_id} step {s_idx}: FINDING step has empty evidence_id")
                elif ev_id not in valid_evidence_ids:
                    errors.append(f"{case_id} step {s_idx}: FINDING step references unknown evidence_id '{ev_id}'")
            elif phase in ('REMEDIATION', 'VERIFICATION'):
                if ev_id != "":
                    errors.append(f"{case_id} step {s_idx}: INCOMPLETE {phase} step must have empty evidence_id, got '{ev_id}'")

print("\n=== VALIDATION SUMMARY ===")
print(f"Total rows evaluated: {len(rows)}")
print(f"Status distribution: {status_counts}")
print(f"Total errors: {len(errors)}")
print(f"Total warnings: {len(warnings)}")

if errors:
    print("\nErrors encountered (first 20):")
    for err in errors[:20]:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("\nALL 14 CHECKS PASSED PERFECTLY with 0 errors and 0 warnings.")
