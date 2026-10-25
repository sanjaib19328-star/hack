import os
import shutil
import zipfile
import subprocess
import sys
import json
import csv
import hashlib

zip_path = os.path.abspath('scratch/stage3_7/patched_code.zip')
gate_dir = os.path.abspath('scratch/stage3_8/extracted_gate')

print(f"=== 1. Extracting {zip_path} into {gate_dir} ===")
if os.path.exists(gate_dir):
    shutil.rmtree(gate_dir)
os.makedirs(gate_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(gate_dir)

print(f"Extracted files: {os.listdir(gate_dir)}")

# Copy read-only dataset into extracted gate folder
shutil.copytree('dataset', os.path.join(gate_dir, 'dataset'))
print("Copied dataset into gate folder.")

# === 2. Verify Code Logic in Extracted Package ===
extracted_main = os.path.join(gate_dir, 'code', 'main.py')
with open(extracted_main, 'r', encoding='utf-8') as f:
    main_code = f.read()

has_search_doc_fix = 'search_documents_primary' in main_code and 'source_resource_id' in main_code
has_strict_fallback_policy = 'elif not (findings or verifications) and fallback_acc:' in main_code
has_no_sample_leakage = 'sample_output' not in main_code and 'sample_baseline' not in main_code

print("\n=== Code Integrity Checks in Extracted Package ===")
print(f"  search_documents_primary mapping present: {has_search_doc_fix}")
print(f"  Strict account fallback policy present:   {has_strict_fallback_policy}")
print(f"  Zero sample output leakage:              {has_no_sample_leakage}")

assert has_search_doc_fix, "Missing search_documents_primary fix in package!"
assert has_strict_fallback_policy, "Missing strict fallback policy in package!"
assert has_no_sample_leakage, "Sample output leakage detected in package!"

# === 3. Run Packaged Tests in Strict Isolation ===
print("\n=== Running Packaged Unit Tests (test_core_engine.py) in Isolation ===")
env = os.environ.copy()
env['PYTHONPATH'] = os.path.join(gate_dir, 'code')

test_proc = subprocess.run(
    [sys.executable, os.path.join(gate_dir, 'code', 'evaluation', 'test_core_engine.py')],
    cwd=gate_dir,
    capture_output=True,
    text=True,
    env=env
)

print("Test Exit Code:", test_proc.returncode)
print("Stdout:", test_proc.stdout.strip())
print("Stderr:", test_proc.stderr.strip())

assert test_proc.returncode == 0, "Packaged unit tests failed in isolation!"

# === 4. Run Sample Execution in Strict Isolation ===
print("\n=== Executing Sample Audit from Extracted Package ===")
sample_out = os.path.join(gate_dir, 'gate_sample_pred.csv')
sample_reqs = os.path.join(gate_dir, 'dataset', 'sample_deletion_requests.csv')

audit_sample_proc = subprocess.run(
    [sys.executable, os.path.join(gate_dir, 'code', 'main.py'), sample_reqs, sample_out],
    cwd=gate_dir,
    capture_output=True,
    text=True,
    env=env
)

print("Sample Audit Exit Code:", audit_sample_proc.returncode)
print("Stdout:", audit_sample_proc.stdout.strip())

assert audit_sample_proc.returncode == 0, "Sample audit failed!"

# === 5. Recompute Sample Metrics from Extracted Output ===
def norm_s(val): return str(val).strip().lower()
def norm_upper(val): return str(val).strip().upper()

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

truth_path = os.path.join(gate_dir, 'dataset', 'sample_output.csv')
with open(truth_path, 'r', encoding='utf-8') as f:
    truths = {r['case_id']: {'status': r['deletion_status'].strip(), 'steps': json.loads(r['steps_json'])} for r in csv.DictReader(f)}

with open(sample_out, 'r', encoding='utf-8') as f:
    preds = {r['case_id']: {'status': r['deletion_status'].strip(), 'steps': json.loads(r['steps_json'])} for r in csv.DictReader(f)}

status_matches = sum(1 for cid in truths if truths[cid]['status'] == preds.get(cid, {}).get('status'))
exact_matches = sum(1 for cid in truths if truths[cid]['status'] == preds.get(cid, {}).get('status') and truths[cid]['steps'] == preds.get(cid, {}).get('steps'))

sem_tp = 0
strict_tp = 0
total_p = sum(len(p['steps']) for p in preds.values())
total_t = sum(len(t['steps']) for t in truths.values())

correct_fields = 0
total_fields = 0

for cid, t_data in truths.items():
    p_data = preds[cid]
    t_steps = t_data['steps']
    p_steps = p_data['steps']
    
    # Semantic matching
    matched_t_sem = set()
    pairs = []
    for p_idx, ps in enumerate(p_steps):
        pkey = semantic_key(ps)
        for t_idx, ts in enumerate(t_steps):
            if t_idx not in matched_t_sem and pkey == semantic_key(ts):
                matched_t_sem.add(t_idx)
                pairs.append((p_idx, t_idx))
                sem_tp += 1
                break
                
    # Strict matching
    matched_t_str = set()
    for p_idx, ps in enumerate(p_steps):
        pkey = strict_key(ps)
        for t_idx, ts in enumerate(t_steps):
            if t_idx not in matched_t_str and pkey == strict_key(ts):
                matched_t_str.add(t_idx)
                strict_tp += 1
                break
                
    for p_idx, t_idx in pairs:
        ps, ts = p_steps[p_idx], t_steps[t_idx]
        for fld in ['step_no', 'phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id']:
            if str(ps.get(fld, '')).strip() == str(ts.get(fld, '')).strip():
                correct_fields += 1
                
    missing = len(t_steps) - len(pairs)
    extra = len(p_steps) - len(pairs)
    total_fields += 7 * (len(pairs) + missing + extra)

sem_prec = sem_tp / total_p if total_p > 0 else 0
sem_rec = sem_tp / total_t if total_t > 0 else 0
sem_f1 = 2 * sem_prec * sem_rec / (sem_prec + sem_rec) if (sem_prec + sem_rec) > 0 else 0
strict_prec = strict_tp / total_p if total_p > 0 else 0
strict_rec = strict_tp / total_t if total_t > 0 else 0
strict_f1 = 2 * strict_prec * strict_rec / (strict_prec + strict_rec) if (strict_prec + strict_rec) > 0 else 0
aligned_acc = correct_fields / total_fields if total_fields > 0 else 0

print("\n=== Recomputed Sample Metrics from Packaged Output ===")
print(f"  Status Accuracy:            {status_matches}/32 ({status_matches/32*100:.2f}%)")
print(f"  Exact Sequence Accuracy:    {exact_matches}/32 ({exact_matches/32*100:.2f}%)")
print(f"  Semantic Precision:         {sem_tp}/{total_p} ({sem_prec*100:.2f}%)")
print(f"  Semantic Recall:            {sem_tp}/{total_t} ({sem_rec*100:.2f}%)")
print(f"  Semantic F1-Score:          {sem_f1*100:.2f}%")
print(f"  Strict Precision:           {strict_tp}/{total_p} ({strict_prec*100:.2f}%)")
print(f"  Strict Recall:              {strict_tp}/{total_t} ({strict_rec*100:.2f}%)")
print(f"  Strict F1-Score:            {strict_f1*100:.2f}%")
print(f"  Key-Aligned Field Accuracy: {correct_fields}/{total_fields} ({aligned_acc*100:.2f}%)")

# === 6. Verify case_06 and Ambiguous Cases ===
print("\n=== Verifying case_06 and Ambiguous Cases ===")
c06_pred = preds['case_06']
c06_truth = truths['case_06']
c06_exact = (c06_pred['status'] == c06_truth['status'] and c06_pred['steps'] == c06_truth['steps'])
print(f"  case_06 100% exact match: {c06_exact}")
acc_06_step = next((s for s in c06_pred['steps'] if s['system_id'] == 'account_service'), None)
print(f"  case_06 account_service verification: {acc_06_step}")

ambiguous_cases = ['case_07', 'case_08', 'case_09', 'case_10', 'case_18', 'case_20', 'case_22', 'case_23', 'case_25', 'case_28', 'case_29', 'case_31', 'case_32']
ambig_clean = True
for cid in ambiguous_cases:
    acc_steps = [s for s in preds[cid]['steps'] if s['system_id'] == 'account_service']
    if acc_steps:
        print(f"  WARNING: {cid} contains unexpected account_service step: {acc_steps}")
        ambig_clean = False

print(f"  All {len(ambiguous_cases)} ambiguous cases free of speculative account IDs: {ambig_clean}")

# === 7. Run Full 518-Case Execution from Extracted Package ===
print("\n=== Executing Full 518-Case Audit from Extracted Package ===")
full_out = os.path.join(gate_dir, 'gate_full_output.csv')
full_reqs = os.path.join(gate_dir, 'dataset', 'deletion_requests.csv')

audit_full_proc = subprocess.run(
    [sys.executable, os.path.join(gate_dir, 'code', 'main.py'), full_reqs, full_out],
    cwd=gate_dir,
    capture_output=True,
    text=True,
    env=env
)

print("Full Audit Exit Code:", audit_full_proc.returncode)
print("Stdout:", audit_full_proc.stdout.strip())
assert audit_full_proc.returncode == 0, "Full audit failed!"

# Compare with scratch/candidate_output.csv
cand_out_path = 'scratch/candidate_output.csv'
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

cand_hash = sha256_file(cand_out_path)
gate_hash = sha256_file(full_out)

print(f"\nCandidate Output Hash: {cand_hash}")
print(f"Gate Output Hash:      {gate_hash}")
print(f"Hash Match:            {cand_hash == gate_hash}")

with open(cand_out_path, 'r', encoding='utf-8') as f:
    cand_rows = list(csv.reader(f))
with open(full_out, 'r', encoding='utf-8') as f:
    gate_rows = list(csv.reader(f))

print(f"Candidate Row Count:   {len(cand_rows)}")
print(f"Gate Row Count:        {len(gate_rows)}")
print(f"Exact Content Match:   {cand_rows == gate_rows}")

assert cand_hash == gate_hash, "Hash mismatch on 518-case output!"
assert cand_rows == gate_rows, "Content mismatch on 518-case output!"

print("\nSUCCESS: All release gate verification checks passed with 100% precision!")
