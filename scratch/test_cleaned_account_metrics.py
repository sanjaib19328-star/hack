import csv
import json
import collections

# Load truth
with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

# Let's inspect candidate_sample_pred.csv
with open("scratch/candidate_sample_pred.csv", "r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

target_10 = ["case_09", "case_18", "case_20", "case_22", "case_23", "case_25", "case_28", "case_29", "case_31", "case_32"]

# If we remove the ungrounded account_service step from target_10:
cleaned_pred = {}
for cid, (stat, steps) in pred.items():
    if cid in target_10:
        new_steps = [s for s in steps if not (s["system_id"] == "account_service" and s["resource_id"].startswith("account_0") or s["resource_id"] in ["account_541", "account_542"])]
        # re-number step_no
        for idx, s in enumerate(new_steps, 1):
            s["step_no"] = idx
        cleaned_pred[cid] = (stat, new_steps)
    else:
        cleaned_pred[cid] = (stat, steps)

# Let's compute semantic and strict metrics on cleaned_pred:
STEP_FIELDS = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]

semantic_tp = 0
total_t_semantic = 0
total_p_semantic = 0

strict_tp = 0
total_t_strict = 0
total_p_strict = 0

exact_matches = 0
status_matches = 0

for cid, (t_stat, t_steps) in truth.items():
    p_stat, p_steps = cleaned_pred[cid]
    if t_stat == p_stat:
        status_matches += 1
    if t_stat == p_stat and t_steps == p_steps:
        exact_matches += 1
        
    t_sem = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in t_steps]
    p_sem = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in p_steps]
    total_t_semantic += len(t_sem)
    total_p_semantic += len(p_sem)
    t_cnt = collections.Counter(t_sem)
    p_cnt = collections.Counter(p_sem)
    for k, cnt in p_cnt.items():
        if k in t_cnt:
            semantic_tp += min(cnt, t_cnt[k])

    t_str = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in t_steps]
    p_str = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in p_steps]
    total_t_strict += len(t_str)
    total_p_strict += len(p_str)
    t_cnt = collections.Counter(t_str)
    p_cnt = collections.Counter(p_str)
    for k, cnt in p_cnt.items():
        if k in t_cnt:
            strict_tp += min(cnt, t_cnt[k])

sem_prec = semantic_tp / total_p_semantic
sem_rec = semantic_tp / total_t_semantic
sem_f1 = 2 * sem_prec * sem_rec / (sem_prec + sem_rec)

strict_prec = strict_tp / total_p_strict
strict_rec = strict_tp / total_t_strict
strict_f1 = 2 * strict_prec * strict_rec / (strict_prec + strict_rec)

print(f"Status Accuracy: {status_matches/32*100:.2f}% ({status_matches}/32)")
print(f"Exact Sequence Accuracy: {exact_matches/32*100:.2f}% ({exact_matches}/32)")
print(f"Semantic Precision: {sem_prec*100:.2f}% ({semantic_tp}/{total_p_semantic})")
print(f"Semantic Recall:    {sem_rec*100:.2f}% ({semantic_tp}/{total_t_semantic})")
print(f"Semantic F1:        {sem_f1*100:.2f}%")
print(f"Strict Precision:   {strict_prec*100:.2f}% ({strict_tp}/{total_p_strict})")
print(f"Strict Recall:      {strict_rec*100:.2f}% ({strict_tp}/{total_t_strict})")
print(f"Strict F1:          {strict_f1*100:.2f}%")
