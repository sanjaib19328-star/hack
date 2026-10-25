"""
Evaluation and Validation Module for HackerRank Orchestrate: Ghost Data Still Exists.

This module provides automated evaluation of predictions against ground truth,
schema validation for submission outputs, and unit regression tests on custom edge cases.

Usage:
    python code/evaluation/main.py --pred output.csv
    python code/evaluation/main.py --pred sample_test_output.csv --truth dataset/sample_output.csv
    python code/evaluation/main.py --test
"""

import sys
import os

# Ensure parent directory (code/) is in sys.path
_parent_code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_code_dir not in sys.path:
    sys.path.insert(0, _parent_code_dir)

import csv
import json
import argparse
from typing import Dict, List, Any, Tuple


VALID_STATUSES = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
VALID_PHASES = {"FINDING", "REMEDIATION", "VERIFICATION"}
STEP_FIELDS = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]


def load_csv(path: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["case_id"]] = {
                "deletion_status": row["deletion_status"],
                "steps": json.loads(row["steps_json"])
            }
    return data


def validate_schema(pred_path: str, expected_count: int = 518) -> List[str]:
    """Validates output format, schema, step sequencing, and phase constraints."""
    errors = []
    if not os.path.exists(pred_path):
        return [f"Prediction file {pred_path} does not exist."]
    
    with open(pred_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if fieldnames != ["case_id", "deletion_status", "steps_json"]:
            errors.append(f"Invalid header: {fieldnames}, expected ['case_id', 'deletion_status', 'steps_json']")
        
        rows = list(reader)
        if expected_count is not None and len(rows) != expected_count:
            errors.append(f"Expected {expected_count} rows, found {len(rows)}")
        
        case_ids = set()
        for idx, row in enumerate(rows):
            cid = row.get("case_id", "")
            if not cid:
                errors.append(f"Row {idx}: missing case_id")
            elif cid in case_ids:
                errors.append(f"Duplicate case_id: {cid}")
            case_ids.add(cid)
            
            status = row.get("deletion_status", "")
            if status not in VALID_STATUSES:
                errors.append(f"Case {cid}: invalid deletion_status '{status}'")
                
            try:
                steps = json.loads(row.get("steps_json", ""))
            except Exception as e:
                errors.append(f"Case {cid}: malformed JSON in steps_json: {e}")
                continue
                
            if not isinstance(steps, list):
                errors.append(f"Case {cid}: steps_json is not a list")
                continue
                
            if status == "NOT_APPLICABLE":
                if len(steps) != 0:
                    errors.append(f"Case {cid}: NOT_APPLICABLE status must have empty steps array, got {len(steps)} steps")
            else:
                if len(steps) == 0:
                    errors.append(f"Case {cid}: {status} status must have non-empty steps")
                    
            phase_order_map = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}
            last_phase_rank = 0
            
            for s_idx, step in enumerate(steps):
                # Step numbering
                if step.get("step_no") != s_idx + 1:
                    errors.append(f"Case {cid}: step {s_idx} has step_no {step.get('step_no')}, expected {s_idx + 1}")
                    
                # Fields check
                for field in STEP_FIELDS:
                    if field not in step:
                        errors.append(f"Case {cid}: step {s_idx + 1} missing field '{field}'")
                        
                phase = step.get("phase")
                if phase not in VALID_PHASES:
                    errors.append(f"Case {cid}: step {s_idx + 1} invalid phase '{phase}'")
                else:
                    curr_rank = phase_order_map[phase]
                    if curr_rank < last_phase_rank:
                        errors.append(f"Case {cid}: phase out of order ({phase} after higher phase)")
                    last_phase_rank = curr_rank
                    
                ev_id = step.get("evidence_id", "")
                if status == "COMPLETE":
                    if not ev_id:
                        errors.append(f"Case {cid}: COMPLETE verification step {s_idx + 1} must cite non-empty evidence_id")
                elif status == "INCOMPLETE":
                    if phase == "FINDING":
                        if not ev_id:
                            errors.append(f"Case {cid}: FINDING step {s_idx + 1} must cite non-empty evidence_id")
                    elif phase in ("REMEDIATION", "VERIFICATION"):
                        if ev_id != "":
                            errors.append(f"Case {cid}: Proposed {phase} step {s_idx + 1} must have empty evidence_id ('')")

    return errors


def evaluate_predictions(pred_path: str, truth_path: str) -> Dict[str, Any]:
    pred_data = load_csv(pred_path)
    truth_data = load_csv(truth_path)
    
    total_cases = len(truth_data)
    status_matches = 0
    exact_sequence_matches = 0
    total_steps_truth = 0
    total_steps_pred = 0
    
    total_fields = 0
    field_matches = 0
    
    mismatches = []
    
    for cid, t_obj in truth_data.items():
        if cid not in pred_data:
            mismatches.append({"case_id": cid, "error": "Missing from predictions"})
            continue
            
        p_obj = pred_data[cid]
        
        # Status match
        total_fields += 1
        if p_obj["deletion_status"] == t_obj["deletion_status"]:
            status_matches += 1
            field_matches += 1
        else:
            mismatches.append({
                "case_id": cid,
                "error": f"Status mismatch: expected {t_obj['deletion_status']}, got {p_obj['deletion_status']}"
            })
            
        t_steps = t_obj["steps"]
        p_steps = p_obj["steps"]
        total_steps_truth += len(t_steps)
        total_steps_pred += len(p_steps)
        
        if t_steps == p_steps:
            exact_sequence_matches += 1
        else:
            if p_obj["deletion_status"] == t_obj["deletion_status"]:
                mismatches.append({
                    "case_id": cid,
                    "error": f"Step sequence mismatch: expected {len(t_steps)} steps, got {len(p_steps)} steps"
                })
                
        # Compare fields across common steps
        for s1, s2 in zip(t_steps, p_steps):
            for f in STEP_FIELDS:
                total_fields += 1
                if s1.get(f) == s2.get(f):
                    field_matches += 1

    metrics = {
        "total_cases": total_cases,
        "status_accuracy": status_matches / total_cases if total_cases > 0 else 0.0,
        "sequence_accuracy": exact_sequence_matches / total_cases if total_cases > 0 else 0.0,
        "field_accuracy": field_matches / total_fields if total_fields > 0 else 0.0,
        "total_fields": total_fields,
        "field_matches": field_matches,
        "status_matches": status_matches,
        "sequence_matches": exact_sequence_matches,
        "mismatches": mismatches
    }
    return metrics


def run_custom_test_cases():
    """Executes at least 3 custom unit tests for critical edge cases."""
    print("Running custom regression and edge case tests...")
    
    # Test Case 1: Non-deletion request text (e.g. data export / invoice request)
    from main import RequestClassifier
    test_text_not_app = "Please provide an export of all my past invoices for tax purposes. Keep the account active."
    is_non_del = RequestClassifier.is_non_deletion(test_text_not_app, "case_999")
    assert is_non_del is True, "Test 1 Failed: RequestClassifier did not detect non-deletion request"
    print("[PASS] Test Case 1: Non-deletion request text correctly classified as NOT_APPLICABLE.")

    # Test Case 2: Historical email alias resolution
    from main import IdentityResolver
    resolver = IdentityResolver("dataset")
    # Resolve historical email address that was changed
    test_email = "o.walker6695@yahoo.com"
    u_id = resolver.resolve_email(test_email)
    assert u_id == "user_523", f"Test 2 Failed: expected user_523, got {u_id}"
    u_info = resolver.get_identities(u_id)
    assert u_info["user_id"] == "user_523"
    assert test_email in u_info["emails"]
    print(f"[PASS] Test Case 2: IdentityResolver accurately linked historical alias {test_email} to {u_id}.")

    # Test Case 3: Proper step sequencing and empty evidence_id for proposed actions
    from main import sort_steps
    raw_steps = [
        {"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_100", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "ev_01"},
        {"step_no": 2, "phase": "FINDING", "system_id": "analytics_platform", "resource_id": "event_log_482", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "ev_02"},
        {"step_no": 3, "phase": "REMEDIATION", "system_id": "analytics_platform", "resource_id": "event_log_482", "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": ""}
    ]
    sorted_steps = sort_steps(raw_steps)
    # Check phase ordering: FINDING (1) -> REMEDIATION (2) -> VERIFICATION (3)
    phases = [s["phase"] for s in sorted_steps]
    assert phases == ["FINDING", "REMEDIATION", "VERIFICATION"], f"Test 3 Failed: sort_steps phase ordering {phases}"
    # Verify that remediation step has empty evidence_id
    rem_step = [s for s in sorted_steps if s["phase"] == "REMEDIATION"][0]
    assert rem_step["evidence_id"] == "", "Test 3 Failed: proposed remediation step must have empty evidence_id"
    print("[PASS] Test Case 3: Step sequencing order (FINDING -> REMEDIATION -> VERIFICATION) and empty evidence_id verified.")

    print("All custom test cases passed successfully!\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Deletion Audit Predictions")
    parser.add_argument("--pred", type=str, default="output.csv", help="Path to predictions CSV")
    parser.add_argument("--truth", type=str, default=None, help="Path to ground truth CSV (e.g. sample_output.csv)")
    parser.add_argument("--expected-count", type=int, default=518, help="Expected row count")
    parser.add_argument("--test", action="store_true", help="Run custom test cases")

    args = parser.parse_args()

    if args.test:
        run_custom_test_cases()
        return

    print(f"=== Validating Schema: {args.pred} ===")
    errors = validate_schema(args.pred, args.expected_count)
    if errors:
        print(f"FAILED: Found {len(errors)} validation errors:")
        for err in errors[:15]:
            print(f"  - {err}")
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more.")
        sys.exit(1)
    else:
        print("Schema Validation: PASSED (100% compliant with challenge contract)")

    if args.truth:
        print(f"\n=== Evaluating Accuracy against: {args.truth} ===")
        metrics = evaluate_predictions(args.pred, args.truth)
        print(f"Total Cases: {metrics['total_cases']}")
        print(f"Status Accuracy: {metrics['status_accuracy'] * 100:.2f}% ({metrics['status_matches']}/{metrics['total_cases']})")
        print(f"Exact Sequence Accuracy: {metrics['sequence_accuracy'] * 100:.2f}% ({metrics['sequence_matches']}/{metrics['total_cases']})")
        print(f"Field-Level Accuracy: {metrics['field_accuracy'] * 100:.2f}% ({metrics['field_matches']}/{metrics['total_fields']})")
        if metrics["mismatches"]:
            print(f"Mismatches ({len(metrics['mismatches'])}):")
            for m in metrics["mismatches"][:5]:
                print(f"  - {m}")


if __name__ == "__main__":
    main()
