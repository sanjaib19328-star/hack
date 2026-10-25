import csv, json

def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

truth = load_csv("dataset/sample_output.csv")
pred = load_csv("scratch/candidate_sample_pred.csv")

total_cases = len(truth)

# 1. Deletion-status accuracy
status_matches = sum(1 for cid in truth if truth[cid][0] == pred.get(cid, ('', []))[0])
status_acc = status_matches / total_cases

# 2. Exact ordered-step accuracy
exact_matches = sum(1 for cid in truth if truth[cid][0] == pred.get(cid, ('', []))[0] and truth[cid][1] == pred.get(cid, ('', []))[1])
exact_acc = exact_matches / total_cases

# 3. Step-level Semantic Precision, Recall, F1
# Matching key: (phase, system_id, resource_id, operation, state)
total_t_semantic = 0
total_p_semantic = 0
semantic_tp = 0

# 4. Step-level Strict Precision, Recall, F1
# Matching key: (phase, system_id, resource_id, operation, state, evidence_id)
total_t_strict = 0
total_p_strict = 0
strict_tp = 0

# 5. Field-level evaluations
# Positional evaluator method
pos_fields_num = 0
pos_fields_den = 0

# Aligned field method
aligned_fields_num = 0
aligned_fields_den = 0

for cid, (t_stat, t_steps) in truth.items():
    p_stat, p_steps = pred.get(cid, ('', []))
    
    # Status field
    pos_fields_den += 1
    aligned_fields_den += 1
    if t_stat == p_stat:
        pos_fields_num += 1
        aligned_fields_num += 1
        
    # Semantic sets
    t_sem = [f"{s['phase']}|{s['system_id']}|{s['resource_id']}|{s['operation']}|{s['state']}" for s in t_steps]
    p_sem = [f"{s['phase']}|{s['system_id']}|{s['resource_id']}|{s['operation']}|{s['state']}" for s in p_steps]
    total_t_semantic += len(t_sem)
    total_p_semantic += len(p_sem)
    
    # Multiset intersection for TP
    t_sem_counts = {}
    for k in t_sem: t_sem_counts[k] = t_sem_counts.get(k, 0) + 1
    for k in p_sem:
        if t_sem_counts.get(k, 0) > 0:
            semantic_tp += 1
            t_sem_counts[k] -= 1

    # Strict sets (including evidence_id)
    t_str = [f"{s['phase']}|{s['system_id']}|{s['resource_id']}|{s['operation']}|{s['state']}|{s['evidence_id']}" for s in t_steps]
    p_str = [f"{s['phase']}|{s['system_id']}|{s['resource_id']}|{s['operation']}|{s['state']}|{s['evidence_id']}" for s in p_steps]
    total_t_strict += len(t_str)
    total_p_strict += len(p_str)
    
    t_str_counts = {}
    for k in t_str: t_str_counts[k] = t_str_counts.get(k, 0) + 1
    for k in p_str:
        if t_str_counts.get(k, 0) > 0:
            strict_tp += 1
            t_str_counts[k] -= 1

    # Positional evaluation (code/evaluation/main.py method)
    for s1, s2 in zip(t_steps, p_steps):
        for f in ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]:
            pos_fields_den += 1
            if s1.get(f) == s2.get(f):
                pos_fields_num += 1
                
    # Aligned per-field evaluation:
    # Match steps by (system_id, resource_id, phase)
    # Each ground truth step has 7 fields. Each extra predicted step has 7 fields.
    t_map = {(s['system_id'], s['resource_id'], s['phase']): s for s in t_steps}
    p_map = {(s['system_id'], s['resource_id'], s['phase']): s for s in p_steps}
    
    all_keys = set(t_map.keys()) | set(p_map.keys())
    for k in all_keys:
        s_t = t_map.get(k)
        s_p = p_map.get(k)
        if s_t and s_p:
            for f in ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]:
                aligned_fields_den += 1
                if s_t.get(f) == s_p.get(f):
                    aligned_fields_num += 1
        elif s_t and not s_p:
            # Missing step: 7 fields in ground truth unfulfilled
            aligned_fields_den += 7
        elif s_p and not s_t:
            # Extra step: 7 fields predicted but spurious
            aligned_fields_den += 7

sem_prec = semantic_tp / total_p_semantic if total_p_semantic > 0 else 0.0
sem_rec = semantic_tp / total_t_semantic if total_t_semantic > 0 else 0.0
sem_f1 = (2 * sem_prec * sem_rec) / (sem_prec + sem_rec) if (sem_prec + sem_rec) > 0 else 0.0

strict_prec = strict_tp / total_p_strict if total_p_strict > 0 else 0.0
strict_rec = strict_tp / total_t_strict if total_t_strict > 0 else 0.0
strict_f1 = (2 * strict_prec * strict_rec) / (strict_prec + strict_rec) if (strict_prec + strict_rec) > 0 else 0.0

print("================================================================")
print("             INDEPENDENT VERIFIED METRICS REPORT                ")
print("================================================================")
print(f"Total Cases: {total_cases}")
print(f"1. Deletion-Status Accuracy: {status_acc*100:.2f}% (Numerator: {status_matches}, Denominator: {total_cases})")
print(f"2. Exact Ordered-Step Accuracy: {exact_acc*100:.2f}% (Numerator: {exact_matches}, Denominator: {total_cases})")
print("\n3. Step-Level Semantic Metrics (phase, system_id, resource_id, operation, state):")
print(f"   - Precision: {sem_prec*100:.2f}% ({semantic_tp}/{total_p_semantic})")
print(f"   - Recall:    {sem_rec*100:.2f}% ({semantic_tp}/{total_t_semantic})")
print(f"   - F1-Score:  {sem_f1*100:.2f}%")
print("\n4. Step-Level Strict Metrics (including evidence_id):")
print(f"   - Precision: {strict_prec*100:.2f}% ({strict_tp}/{total_p_strict})")
print(f"   - Recall:    {strict_rec*100:.2f}% ({strict_tp}/{total_t_strict})")
print(f"   - F1-Score:  {strict_f1*100:.2f}%")
print("\n5. Per-Field Accuracy Comparison:")
print(f"   - Evaluator Positional Field Accuracy: {pos_fields_num/pos_fields_den*100:.2f}% ({pos_fields_num}/{pos_fields_den})")
print(f"   - True Aligned Field Accuracy:          {aligned_fields_num/aligned_fields_den*100:.2f}% ({aligned_fields_num}/{aligned_fields_den})")
print("================================================================")
