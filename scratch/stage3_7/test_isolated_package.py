import os
import zipfile
import shutil
import subprocess
import sys
import json
import csv

pkg_zip = os.path.abspath('scratch/stage3_7/patched_code.zip')
isolated_dir = os.path.abspath('scratch/stage3_7/isolated_package')

# 1. Build the zip
print(f"Building {pkg_zip}...")
files_to_pack = [
    ('scratch/stage3_7/patched_main.py', 'code/main.py'),
    ('code/evaluation/main.py', 'code/evaluation/main.py'),
    ('code/evaluation/evaluation_report.md', 'code/evaluation/evaluation_report.md'),
    ('code/evaluation/usage_report.md', 'code/evaluation/usage_report.md'),
    ('code/evaluation/test_core_engine.py', 'code/evaluation/test_core_engine.py'),
    ('README.md', 'README.md')
]

with zipfile.ZipFile(pkg_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for src, arc in files_to_pack:
        z.write(src, arc)
        print(f"  Added {src} -> {arc}")

print(f"Package built. Size: {os.path.getsize(pkg_zip)} bytes.")

# 2. Extract into isolated directory
if os.path.exists(isolated_dir):
    shutil.rmtree(isolated_dir)
os.makedirs(isolated_dir, exist_ok=True)

with zipfile.ZipFile(pkg_zip, 'r') as z:
    z.extractall(isolated_dir)

print(f"Extracted to {isolated_dir}")

# Copy dataset so the isolated environment has the read-only test data
shutil.copytree("dataset", os.path.join(isolated_dir, "dataset"))
print("Copied dataset into isolated directory.")

# 3. Test extracted package in isolation
# Run unit tests from extracted directory
env = os.environ.copy()
env['PYTHONPATH'] = os.path.join(isolated_dir, 'code')

test_proc = subprocess.run(
    [sys.executable, os.path.join(isolated_dir, 'code', 'evaluation', 'test_core_engine.py')],
    cwd=isolated_dir,
    capture_output=True,
    text=True,
    env=env
)

print("\n--- Isolated Package Unit Tests Output ---")
print("Return code:", test_proc.returncode)
print("Stdout:", test_proc.stdout.strip())
print("Stderr:", test_proc.stderr.strip())

# Run sample audit from extracted package
sample_out_isolated = os.path.join(isolated_dir, 'isolated_sample_pred.csv')
sample_reqs = os.path.join(isolated_dir, 'dataset', 'sample_deletion_requests.csv')

audit_proc = subprocess.run(
    [sys.executable, os.path.join(isolated_dir, 'code', 'main.py'), sample_reqs, sample_out_isolated],
    cwd=isolated_dir,
    capture_output=True,
    text=True,
    env=env
)

print("\n--- Isolated Package Sample Audit Execution ---")
print("Return code:", audit_proc.returncode)
print("Stdout:", audit_proc.stdout.strip())
print("Stderr:", audit_proc.stderr.strip())

# 4. Independent evaluation of isolated output
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

truth_path = os.path.join(isolated_dir, 'dataset', 'sample_output.csv')
with open(truth_path, 'r', encoding='utf-8') as f:
    truths = {r['case_id']: {'status': r['deletion_status'].strip(), 'steps': json.loads(r['steps_json'])} for r in csv.DictReader(f)}

with open(sample_out_isolated, 'r', encoding='utf-8') as f:
    preds = {r['case_id']: {'status': r['deletion_status'].strip(), 'steps': json.loads(r['steps_json'])} for r in csv.DictReader(f)}

status_matches = sum(1 for cid in truths if truths[cid]['status'] == preds.get(cid, {}).get('status'))
exact_matches = sum(1 for cid in truths if truths[cid]['status'] == preds.get(cid, {}).get('status') and truths[cid]['steps'] == preds.get(cid, {}).get('steps'))

sem_tp = 0
total_p = 0
total_t = sum(len(t['steps']) for t in truths.values())

correct_fields = 0
total_fields = 0

for cid, t_data in truths.items():
    p_data = preds[cid]
    t_steps = t_data['steps']
    p_steps = p_data['steps']
    total_p += len(p_steps)
    
    matched_t = set()
    pairs = []
    for p_idx, ps in enumerate(p_steps):
        pkey = semantic_key(ps)
        for t_idx, ts in enumerate(t_steps):
            if t_idx not in matched_t and pkey == semantic_key(ts):
                matched_t.add(t_idx)
                pairs.append((p_idx, t_idx))
                sem_tp += 1
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
aligned_acc = correct_fields / total_fields if total_fields > 0 else 0

print("\n--- Isolated Package Metric Results ---")
print(f"Status Accuracy: {status_matches}/32 ({status_matches/32*100:.2f}%)")
print(f"Exact Sequence Accuracy: {exact_matches}/32 ({exact_matches/32*100:.2f}%)")
print(f"Semantic Precision: {sem_tp}/{total_p} ({sem_prec*100:.2f}%)")
print(f"Semantic Recall: {sem_tp}/{total_t} ({sem_rec*100:.2f}%)")
print(f"Semantic F1: {sem_f1*100:.2f}%")
print(f"Key-Aligned Field Accuracy: {correct_fields}/{total_fields} ({aligned_acc*100:.2f}%)")
