import os
import shutil
import zipfile
import subprocess
import json
import csv
import collections

isolated_dir = os.path.abspath("scratch/isolated_pkg_gate")
if os.path.exists(isolated_dir):
    shutil.rmtree(isolated_dir)
os.makedirs(isolated_dir)

zip_path = os.path.abspath("scratch/candidate_code.zip")
print(f"=== 1. Extracting {zip_path} into isolated directory: {isolated_dir} ===")
with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(isolated_dir)

# Copy dataset folder so the environment has all test data locally
dest_dataset = os.path.join(isolated_dir, "dataset")
shutil.copytree("dataset", dest_dataset)

# 2. Run the packaged test suite (code/evaluation/test_core_engine.py) from isolated_dir
print("\n=== 2. Running Packaged Unit & Regression Tests (21 tests) ===")
test_cmd = ["python", os.path.join("code", "evaluation", "test_core_engine.py")]
res_tests = subprocess.run(test_cmd, cwd=isolated_dir, capture_output=True, text=True)
print(f"Test suite exit code: {res_tests.returncode}")
print(f"Test suite stdout:\n{res_tests.stdout.strip()}")
if res_tests.stderr:
    print(f"Test suite stderr:\n{res_tests.stderr.strip()}")

if res_tests.returncode != 0:
    print("FAILED: Packaged test suite failed!")
    exit(1)

# 3. Execute sample requests from isolated_dir
print("\n=== 3. Executing Sample Requests using Packaged Engine ===")
pkg_out_sample = os.path.join(isolated_dir, "pkg_sample_out.csv")
run_cmd = ["python", os.path.join("code", "main.py"), os.path.join("dataset", "sample_deletion_requests.csv"), "pkg_sample_out.csv"]
res_run = subprocess.run(run_cmd, cwd=isolated_dir, capture_output=True, text=True)
print(f"Engine exit code: {res_run.returncode}")
print(f"Engine stdout:\n{res_run.stdout.strip()}")

# 4. Recompute 32-case metrics directly from pkg_sample_out.csv
print("\n=== 4. Recomputing 32-Case Metrics from Fresh Packaged Output ===")
with open(os.path.join(isolated_dir, "dataset", "sample_output.csv"), "r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open(pkg_out_sample, "r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

status_matches = sum(1 for cid in truth if truth[cid][0] == pred.get(cid, ("", []))[0])
exact_matches = sum(1 for cid in truth if truth[cid][0] == pred.get(cid, ("", []))[0] and truth[cid][1] == pred.get(cid, ("", []))[1])

STEP_FIELDS = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]
pos_field_matches = 0
pos_field_total = 0

semantic_tp = 0
total_t_semantic = 0
total_p_semantic = 0

strict_tp = 0
total_t_strict = 0
total_p_strict = 0

aligned_matches = 0
aligned_total = 0

for cid, (t_stat, t_steps) in truth.items():
    p_stat, p_steps = pred.get(cid, ("", []))
    
    # Positional
    pos_field_total += 1
    if t_stat == p_stat:
        pos_field_matches += 1
    for s1, s2 in zip(t_steps, p_steps):
        for f in STEP_FIELDS:
            pos_field_total += 1
            if s1.get(f) == s2.get(f):
                pos_field_matches += 1

    # Semantic
    t_sem = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in t_steps]
    p_sem = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in p_steps]
    total_t_semantic += len(t_sem)
    total_p_semantic += len(p_sem)
    t_cnt = collections.Counter(t_sem)
    p_cnt = collections.Counter(p_sem)
    for k, cnt in p_cnt.items():
        if k in t_cnt:
            semantic_tp += min(cnt, t_cnt[k])

    # Strict
    t_str = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in t_steps]
    p_str = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in p_steps]
    total_t_strict += len(t_str)
    total_p_strict += len(p_str)
    t_cnt = collections.Counter(t_str)
    p_cnt = collections.Counter(p_str)
    for k, cnt in p_cnt.items():
        if k in t_cnt:
            strict_tp += min(cnt, t_cnt[k])

    # Aligned Field
    aligned_total += 1
    if t_stat == p_stat:
        aligned_matches += 1
    t_by_k = collections.defaultdict(list)
    for s in t_steps:
        t_by_k[(s["system_id"], s["resource_id"], s["phase"])].append(s)
    p_by_k = collections.defaultdict(list)
    for s in p_steps:
        p_by_k[(s["system_id"], s["resource_id"], s["phase"])].append(s)
    all_k = set(t_by_k.keys()) | set(p_by_k.keys())
    for k in all_k:
        t_l = t_by_k.get(k, [])
        p_l = p_by_k.get(k, [])
        for idx in range(max(len(t_l), len(p_l))):
            aligned_total += 7
            if idx < len(t_l) and idx < len(p_l):
                for fld in STEP_FIELDS:
                    if t_l[idx].get(fld) == p_l[idx].get(fld):
                        aligned_matches += 1

sem_prec = semantic_tp / total_p_semantic if total_p_semantic else 0
sem_rec = semantic_tp / total_t_semantic if total_t_semantic else 0
sem_f1 = 2 * sem_prec * sem_rec / (sem_prec + sem_rec) if (sem_prec + sem_rec) else 0

strict_prec = strict_tp / total_p_strict if total_p_strict else 0
strict_rec = strict_tp / total_t_strict if total_t_strict else 0
strict_f1 = 2 * strict_prec * strict_rec / (strict_prec + strict_rec) if (strict_prec + strict_rec) else 0

pos_acc = pos_field_matches / pos_field_total if pos_field_total else 0
aligned_acc = aligned_matches / aligned_total if aligned_total else 0

print(f"Status Accuracy:           {status_matches/32*100:.2f}% ({status_matches}/32)")
print(f"Exact Sequence Accuracy:   {exact_matches/32*100:.2f}% ({exact_matches}/32)")
print(f"Semantic Step Precision:   {sem_prec*100:.2f}% ({semantic_tp}/{total_p_semantic})")
print(f"Semantic Step Recall:      {sem_rec*100:.2f}% ({semantic_tp}/{total_t_semantic})")
print(f"Semantic Step F1-Score:    {sem_f1*100:.2f}%")
print(f"Strict Step Precision:     {strict_prec*100:.2f}% ({strict_tp}/{total_p_strict})")
print(f"Strict Step Recall:        {strict_rec*100:.2f}% ({strict_tp}/{total_t_strict})")
print(f"Strict Step F1-Score:      {strict_f1*100:.2f}%")
print(f"Positional Field Accuracy: {pos_acc*100:.2f}% ({pos_field_matches}/{pos_field_total})")
print(f"Key-Aligned Field Accuracy:{aligned_acc*100:.2f}% ({aligned_matches}/{aligned_total})")

# 5. Schema validation using packaged evaluator
print("\n=== 5. Schema Validation using Packaged Evaluator ===")
val_cmd = ["python", os.path.join("code", "evaluation", "main.py"), "--pred", "pkg_sample_out.csv", "--expected-count", "32"]
res_val = subprocess.run(val_cmd, cwd=isolated_dir, capture_output=True, text=True)
print(f"Validation stdout:\n{res_val.stdout.strip()}")

# Cleanup
shutil.rmtree(isolated_dir)
print("\nCleaned up isolated directory. Package verification COMPLETE!")
