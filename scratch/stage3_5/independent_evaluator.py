import csv
import json
import os
from collections import Counter

def load_csv(path):
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"]
            data[cid] = {
                "status": row["deletion_status"].strip(),
                "steps": json.loads(row["steps_json"])
            }
    return data

def norm_s(val):
    return str(val).strip().lower()

def norm_upper(val):
    return str(val).strip().upper()

def semantic_key(step):
    return (
        norm_upper(step.get("phase", "")),
        norm_s(step.get("system_id", "")),
        norm_s(step.get("resource_id", "")),
        norm_upper(step.get("operation", "")),
        norm_upper(step.get("state", ""))
    )

def strict_key(step):
    return (
        norm_upper(step.get("phase", "")),
        norm_s(step.get("system_id", "")),
        norm_s(step.get("resource_id", "")),
        norm_upper(step.get("operation", "")),
        norm_upper(step.get("state", "")),
        norm_s(step.get("evidence_id", ""))
    )

def evaluate(pred_path, truth_path):
    preds = load_csv(pred_path)
    truths = load_csv(truth_path)

    case_ids = sorted(truths.keys(), key=lambda x: int(x.split('_')[1]))

    status_correct = 0
    exact_seq_correct = 0

    total_pred_steps = 0
    total_truth_steps = 0

    semantic_tp = 0
    strict_tp = 0

    total_aligned_fields_correct = 0
    total_aligned_fields_denom = 0

    # For reporting mismatches
    sem_unmatched_preds = []
    sem_unmatched_truths = []
    strict_mismatches = []

    for cid in case_ids:
        p_data = preds.get(cid)
        t_data = truths[cid]

        # 1. Status accuracy
        st_match = (p_data["status"] == t_data["status"])
        if st_match:
            status_correct += 1

        p_steps = p_data["steps"]
        t_steps = t_data["steps"]

        total_pred_steps += len(p_steps)
        total_truth_steps += len(t_steps)

        # 2. Exact sequence match
        # Exact if status matches, lengths match, and all fields in identical order match
        is_exact = False
        if st_match and len(p_steps) == len(t_steps):
            steps_match = True
            for i in range(len(p_steps)):
                ps = p_steps[i]
                ts = t_steps[i]
                for f in ["phase", "system_id", "resource_id", "operation", "state", "evidence_id", "step_no"]:
                    if str(ps.get(f, "")).strip() != str(ts.get(f, "")).strip():
                        steps_match = False
                        break
                if not steps_match:
                    break
            is_exact = steps_match

        if is_exact:
            exact_seq_correct += 1

        # 3. Semantic 1-to-1 multiset matching
        matched_t_indices_sem = set()
        matched_pairs_sem = [] # (p_idx, t_idx)

        for p_idx, ps in enumerate(p_steps):
            pkey = semantic_key(ps)
            found_t = None
            for t_idx, ts in enumerate(t_steps):
                if t_idx in matched_t_indices_sem:
                    continue
                if pkey == semantic_key(ts):
                    found_t = t_idx
                    break
            if found_t is not None:
                matched_t_indices_sem.add(found_t)
                matched_pairs_sem.append((p_idx, found_t))
                semantic_tp += 1
            else:
                sem_unmatched_preds.append((cid, ps))

        for t_idx, ts in enumerate(t_steps):
            if t_idx not in matched_t_indices_sem:
                sem_unmatched_truths.append((cid, ts))

        # 4. Strict 1-to-1 multiset matching
        matched_t_indices_strict = set()
        for p_idx, ps in enumerate(p_steps):
            pkey = strict_key(ps)
            found_t = None
            for t_idx, ts in enumerate(t_steps):
                if t_idx in matched_t_indices_strict:
                    continue
                if pkey == strict_key(ts):
                    found_t = t_idx
                    break
            if found_t is not None:
                matched_t_indices_strict.add(found_t)
                strict_tp += 1
            else:
                strict_mismatches.append((cid, ps))

        # 5. Key-Aligned Field Accuracy with explicit penalties
        # Fields: step_no, phase, system_id, resource_id, operation, state, evidence_id (7 fields)
        case_fields_correct = 0
        for p_idx, t_idx in matched_pairs_sem:
            ps = p_steps[p_idx]
            ts = t_steps[t_idx]
            if ps.get("step_no") == ts.get("step_no"): case_fields_correct += 1
            if norm_upper(ps.get("phase", "")) == norm_upper(ts.get("phase", "")): case_fields_correct += 1
            if norm_s(ps.get("system_id", "")) == norm_s(ts.get("system_id", "")): case_fields_correct += 1
            if norm_s(ps.get("resource_id", "")) == norm_s(ts.get("resource_id", "")): case_fields_correct += 1
            if norm_upper(ps.get("operation", "")) == norm_upper(ts.get("operation", "")): case_fields_correct += 1
            if norm_upper(ps.get("state", "")) == norm_upper(ts.get("state", "")): case_fields_correct += 1
            if norm_s(ps.get("evidence_id", "")) == norm_s(ts.get("evidence_id", "")): case_fields_correct += 1

        # Denominator for this case includes matched pairs + missing steps + extra steps
        missing_count = len(t_steps) - len(matched_pairs_sem)
        extra_count = len(p_steps) - len(matched_pairs_sem)
        case_denom = 7 * (len(matched_pairs_sem) + missing_count + extra_count)

        total_aligned_fields_correct += case_fields_correct
        total_aligned_fields_denom += case_denom

    # Metric computations
    status_acc = status_correct / len(case_ids)
    exact_acc = exact_seq_correct / len(case_ids)

    sem_prec = semantic_tp / total_pred_steps if total_pred_steps > 0 else 0.0
    sem_rec = semantic_tp / total_truth_steps if total_truth_steps > 0 else 0.0
    sem_f1 = (2 * sem_prec * sem_rec / (sem_prec + sem_rec)) if (sem_prec + sem_rec) > 0 else 0.0

    strict_prec = strict_tp / total_pred_steps if total_pred_steps > 0 else 0.0
    strict_rec = strict_tp / total_truth_steps if total_truth_steps > 0 else 0.0
    strict_f1 = (2 * strict_prec * strict_rec / (strict_prec + strict_rec)) if (strict_prec + strict_rec) > 0 else 0.0

    aligned_field_acc = total_aligned_fields_correct / total_aligned_fields_denom if total_aligned_fields_denom > 0 else 0.0

    return {
        "status_accuracy": (status_correct, len(case_ids), status_acc),
        "exact_sequence_accuracy": (exact_seq_correct, len(case_ids), exact_acc),
        "total_pred_steps": total_pred_steps,
        "total_truth_steps": total_truth_steps,
        "semantic_tp": semantic_tp,
        "semantic_precision": sem_prec,
        "semantic_recall": sem_rec,
        "semantic_f1": sem_f1,
        "strict_tp": strict_tp,
        "strict_precision": strict_prec,
        "strict_recall": strict_rec,
        "strict_f1": strict_f1,
        "aligned_field_accuracy": (total_aligned_fields_correct, total_aligned_fields_denom, aligned_field_acc),
        "sem_unmatched_preds": sem_unmatched_preds,
        "sem_unmatched_truths": sem_unmatched_truths,
    }

if __name__ == "__main__":
    res = evaluate("scratch/candidate_sample_pred.csv", "dataset/sample_output.csv")
    print("================ INDEPENDENT EVALUATION REPORT ================")
    print(f"Status Accuracy: {res['status_accuracy'][0]}/{res['status_accuracy'][1]} ({res['status_accuracy'][2]*100:.2f}%)")
    print(f"Exact Ordered Sequence: {res['exact_sequence_accuracy'][0]}/{res['exact_sequence_accuracy'][1]} ({res['exact_sequence_accuracy'][2]*100:.2f}%)")
    print(f"Total Predicted Steps: {res['total_pred_steps']}, Total Truth Steps: {res['total_truth_steps']}")
    print(f"Semantic TP: {res['semantic_tp']}")
    print(f"Semantic Precision: {res['semantic_tp']}/{res['total_pred_steps']} = {res['semantic_precision']*100:.2f}%")
    print(f"Semantic Recall: {res['semantic_tp']}/{res['total_truth_steps']} = {res['semantic_recall']*100:.2f}%")
    print(f"Semantic F1: {res['semantic_f1']*100:.2f}%")
    print(f"Strict TP: {res['strict_tp']}")
    print(f"Strict Precision: {res['strict_tp']}/{res['total_pred_steps']} = {res['strict_precision']*100:.2f}%")
    print(f"Strict Recall: {res['strict_tp']}/{res['total_truth_steps']} = {res['strict_recall']*100:.2f}%")
    print(f"Strict F1: {res['strict_f1']*100:.2f}%")
    print(f"Aligned Field Accuracy (with penalties): {res['aligned_field_accuracy'][0]}/{res['aligned_field_accuracy'][1]} = {res['aligned_field_accuracy'][2]*100:.2f}%")
    print("\nSemantic Unmatched Predictions (False Positives):", len(res['sem_unmatched_preds']))
    for cid, ps in res['sem_unmatched_preds']:
        print(f"  {cid}: {ps}")
    print("\nSemantic Unmatched Reference Steps (False Negatives):", len(res['sem_unmatched_truths']))
    for cid, ts in res['sem_unmatched_truths']:
        print(f"  {cid}: {ts}")
