import csv
import json
import collections

# Load ground truth and candidate predictions
with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("scratch/candidate_sample_pred.csv", "r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

print(f"Total truth cases: {len(truth)}")
print(f"Total pred cases: {len(pred)}")

# 1. Status Accuracy
status_matches = sum(1 for cid in truth if truth[cid][0] == pred.get(cid, ("", []))[0])
status_acc = status_matches / len(truth)
print(f"\n1. Status Accuracy: {status_acc * 100:.2f}% ({status_matches}/{len(truth)})")

# 2. Exact Ordered-Step Accuracy
# Matches if status matches AND full ordered steps match exactly
exact_matches = sum(1 for cid in truth if truth[cid][0] == pred.get(cid, ("", []))[0] and truth[cid][1] == pred.get(cid, ("", []))[1])
exact_acc = exact_matches / len(truth)
print(f"2. Exact Ordered-Step Accuracy: {exact_acc * 100:.2f}% ({exact_matches}/{len(truth)})")

# 3. Step-Level Semantic Metrics (phase, system_id, resource_id, operation, state)
# We handle duplicates using multiset / Counter intersection (min(count_t, count_p))
semantic_tp = 0
total_t_semantic = 0
total_p_semantic = 0

for cid, (t_stat, t_steps) in truth.items():
    p_stat, p_steps = pred.get(cid, ("", []))
    
    t_keys = [
        (s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"))
        for s in t_steps
    ]
    p_keys = [
        (s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"))
        for s in p_steps
    ]
    
    t_counter = collections.Counter(t_keys)
    p_counter = collections.Counter(p_keys)
    
    total_t_semantic += len(t_keys)
    total_p_semantic += len(p_keys)
    
    for k, count in p_counter.items():
        if k in t_counter:
            semantic_tp += min(count, t_counter[k])

sem_prec = semantic_tp / total_p_semantic if total_p_semantic else 0
sem_rec = semantic_tp / total_t_semantic if total_t_semantic else 0
sem_f1 = (2 * sem_prec * sem_rec / (sem_prec + sem_rec)) if (sem_prec + sem_rec) else 0

print(f"\n3. Semantic Step Metrics:")
print(f"   - True Positives: {semantic_tp}")
print(f"   - Total Truth Steps: {total_t_semantic}")
print(f"   - Total Pred Steps:  {total_p_semantic}")
print(f"   - Precision: {sem_prec * 100:.2f}% ({semantic_tp}/{total_p_semantic})")
print(f"   - Recall:    {sem_rec * 100:.2f}% ({semantic_tp}/{total_t_semantic})")
print(f"   - F1-Score:  {sem_f1 * 100:.2f}%")

# 4. Step-Level Strict Metrics (including evidence_id)
strict_tp = 0
total_t_strict = 0
total_p_strict = 0

for cid, (t_stat, t_steps) in truth.items():
    p_stat, p_steps = pred.get(cid, ("", []))
    
    t_keys = [
        (s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"), s.get("evidence_id"))
        for s in t_steps
    ]
    p_keys = [
        (s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"), s.get("evidence_id"))
        for s in p_steps
    ]
    
    t_counter = collections.Counter(t_keys)
    p_counter = collections.Counter(p_keys)
    
    total_t_strict += len(t_keys)
    total_p_strict += len(p_keys)
    
    for k, count in p_counter.items():
        if k in t_counter:
            strict_tp += min(count, t_counter[k])

strict_prec = strict_tp / total_p_strict if total_p_strict else 0
strict_rec = strict_tp / total_t_strict if total_t_strict else 0
strict_f1 = (2 * strict_prec * strict_rec / (strict_prec + strict_rec)) if (strict_prec + strict_rec) else 0

print(f"\n4. Strict Step Metrics (including evidence_id):")
print(f"   - True Positives: {strict_tp}")
print(f"   - Total Truth Steps: {total_t_strict}")
print(f"   - Total Pred Steps:  {total_p_strict}")
print(f"   - Precision: {strict_prec * 100:.2f}% ({strict_tp}/{total_p_strict})")
print(f"   - Recall:    {strict_rec * 100:.2f}% ({strict_tp}/{total_t_strict})")
print(f"   - F1-Score:  {strict_f1 * 100:.2f}%")

# 5. Positional Field Accuracy (as in code/evaluation/main.py)
STEP_FIELDS = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]
pos_field_matches = 0
pos_field_total = 0

for cid, (t_stat, t_steps) in truth.items():
    p_stat, p_steps = pred.get(cid, ("", []))
    pos_field_total += 1
    if t_stat == p_stat:
        pos_field_matches += 1
    
    for s1, s2 in zip(t_steps, p_steps):
        for fld in STEP_FIELDS:
            pos_field_total += 1
            if s1.get(fld) == s2.get(fld):
                pos_field_matches += 1

pos_acc = pos_field_matches / pos_field_total if pos_field_total else 0
print(f"\n5. Positional Field Accuracy (Evaluator method): {pos_acc * 100:.2f}% ({pos_field_matches}/{pos_field_total})")

# 6. Key-Aligned Field Accuracy
# Align steps by semantic key (system_id, resource_id, phase) or order, comparing all 7 fields
aligned_matches = 0
aligned_total = 0

for cid, (t_stat, t_steps) in truth.items():
    p_stat, p_steps = pred.get(cid, ("", []))
    aligned_total += 1
    if t_stat == p_stat:
        aligned_matches += 1
    
    # Map steps by key: (system_id, resource_id, phase)
    t_by_key = collections.defaultdict(list)
    for s in t_steps:
        k = (s.get("system_id"), s.get("resource_id"), s.get("phase"))
        t_by_key[k].append(s)
        
    p_by_key = collections.defaultdict(list)
    for s in p_steps:
        k = (s.get("system_id"), s.get("resource_id"), s.get("phase"))
        p_by_key[k].append(s)
        
    all_keys = set(t_by_key.keys()) | set(p_by_key.keys())
    for k in all_keys:
        t_list = t_by_key.get(k, [])
        p_list = p_by_key.get(k, [])
        max_len = max(len(t_list), len(p_list))
        for idx in range(max_len):
            aligned_total += 7  # 7 step fields
            if idx < len(t_list) and idx < len(p_list):
                s1 = t_list[idx]
                s2 = p_list[idx]
                for fld in STEP_FIELDS:
                    if s1.get(fld) == s2.get(fld):
                        aligned_matches += 1
            # Missing or extra steps contribute 0 matches for all 7 fields

aligned_acc = aligned_matches / aligned_total if aligned_total else 0
print(f"6. True Key-Aligned Field Accuracy: {aligned_acc * 100:.2f}% ({aligned_matches}/{aligned_total})")
