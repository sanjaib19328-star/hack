import os
import sys
import shutil
import zipfile
import hashlib
import subprocess

zip_path = 'scratch/stage3_7/patched_code.zip'
extract_dir = 'scratch/stage3_12/extracted'
patched_main_path = 'scratch/stage3_7/patched_main.py'

print("=== STEP 4: VALIDATE THE CODE PACKAGE ===\n")

if os.path.exists(extract_dir):
    shutil.rmtree(extract_dir)
os.makedirs(extract_dir, exist_ok=True)

# 1. Inspect archive entries before extracting
expected_files = {
    'code/main.py',
    'code/evaluation/main.py',
    'code/evaluation/evaluation_report.md',
    'code/evaluation/usage_report.md',
    'code/evaluation/test_core_engine.py',
    'README.md'
}

forbidden_extensions = ('.zip', '.tar', '.gz', '.tgz', '.7z', '.rar', '.pyc', '.exe', '.dll', '.so', '.dylib')

with zipfile.ZipFile(zip_path, 'r') as z:
    infolist = z.infolist()
    actual_names = [info.filename for info in infolist]
    
    print(f"Archive entry count: {len(actual_names)}")
    for name in actual_names:
        print(f"  - {name}")
        
    # Check for path traversal entries
    for name in actual_names:
        if name.startswith('/') or name.startswith('\\') or '..' in name:
            print(f"ERROR: Dangerous path traversal entry detected: {name}")
            sys.exit(1)
            
    # Check for forbidden files (caches, nested archives, executables)
    for name in actual_names:
        if any(name.endswith(ext) for ext in forbidden_extensions):
            print(f"ERROR: Forbidden file type detected: {name}")
            sys.exit(1)
        if '__pycache__' in name:
            print(f"ERROR: __pycache__ cache detected: {name}")
            sys.exit(1)
        if name.startswith('dataset/'):
            print(f"ERROR: dataset file bundled in code.zip: {name}")
            sys.exit(1)
            
    # Compare with expected 6 files
    actual_set = set(actual_names)
    if actual_set != expected_files:
        print(f"ERROR: File list mismatch!")
        print(f"Missing: {expected_files - actual_set}")
        print(f"Extra: {actual_set - expected_files}")
        sys.exit(1)
    else:
        print("\nArchive member check: EXACTLY THE 6 EXPECTED FILES PRESENT. No extra, cache, or nested archives.")

    # Extract
    z.extractall(extract_dir)

print(f"\nExtracted successfully to {extract_dir}.")

# Byte-for-byte check of code/main.py vs scratch/stage3_7/patched_main.py
extracted_main = os.path.join(extract_dir, 'code', 'main.py')
with open(extracted_main, 'rb') as f1, open(patched_main_path, 'rb') as f2:
    data1 = f1.read()
    data2 = f2.read()
    h1 = hashlib.sha256(data1).hexdigest()
    h2 = hashlib.sha256(data2).hexdigest()
    match = (data1 == data2)
    print(f"\nExtracted code/main.py: {len(data1):,} bytes, SHA-256: {h1}")
    print(f"Source patched_main.py: {len(data2):,} bytes, SHA-256: {h2}")
    print(f"Byte-for-byte match: {match}")
    if not match:
        print("ERROR: Byte-for-byte mismatch between packaged code/main.py and patched_main.py!")
        sys.exit(1)

# Copy dataset into extract_dir/dataset so tests and engine can run self-contained
repo_dataset = os.path.abspath('dataset')
extracted_dataset = os.path.join(extract_dir, 'dataset')
print(f"\nSetting up dataset copy in {extracted_dataset} for self-contained execution...")
shutil.copytree(repo_dataset, extracted_dataset)

# 2. Run unit tests in isolated extraction directory
print("\n--- RUNNING UNIT TESTS IN ISOLATED EXTRACTION DIRECTORY ---")
test_script = os.path.join('code', 'evaluation', 'test_core_engine.py')
test_cmd = [sys.executable, test_script]
test_res = subprocess.run(test_cmd, cwd=extract_dir, capture_output=True, text=True)

print(f"Command: python {test_script}")
print(f"Working Directory: {os.path.abspath(extract_dir)}")
print(f"Exit Code: {test_res.returncode}")
print("STDOUT:\n" + test_res.stdout)
if test_res.stderr:
    print("STDERR:\n" + test_res.stderr)

if test_res.returncode != 0:
    print("ERROR: Packaged unit tests failed!")
    sys.exit(1)

# 3. Run sample evaluation in isolated directory
print("\n--- RUNNING SAMPLE EVALUATION IN ISOLATED EXTRACTION DIRECTORY ---")
sample_out = os.path.join(extract_dir, 'sample_pred.csv')
run_main_sample_cmd = [
    sys.executable,
    os.path.join('code', 'main.py'),
    os.path.join('dataset', 'sample_deletion_requests.csv'),
    'sample_pred.csv'
]
run_sample_res = subprocess.run(run_main_sample_cmd, cwd=extract_dir, capture_output=True, text=True)
print(f"Command: python code/main.py dataset/sample_deletion_requests.csv sample_pred.csv")
print(f"Exit Code: {run_sample_res.returncode}")
if run_sample_res.stdout:
    print("STDOUT: " + run_sample_res.stdout.strip())
if run_sample_res.stderr:
    print("STDERR: " + run_sample_res.stderr.strip())

eval_cmd = [
    sys.executable,
    os.path.join('code', 'evaluation', 'main.py'),
    '--pred', 'sample_pred.csv',
    '--truth', os.path.join('dataset', 'sample_output.csv')
]
eval_res = subprocess.run(eval_cmd, cwd=extract_dir, capture_output=True, text=True)
print(f"\nEvaluation Output:\n{eval_res.stdout}")
if eval_res.stderr:
    print(f"Evaluation Stderr:\n{eval_res.stderr}")

# 4. Run full 518-case execution in isolated directory
print("\n--- RUNNING FULL 518-CASE EXECUTION IN ISOLATED EXTRACTION DIRECTORY ---")
full_out = os.path.join(extract_dir, 'output.csv')
run_full_cmd = [
    sys.executable,
    os.path.join('code', 'main.py'),
    os.path.join('dataset', 'deletion_requests.csv'),
    'output.csv'
]
run_full_res = subprocess.run(run_full_cmd, cwd=extract_dir, capture_output=True, text=True)
print(f"Command: python code/main.py dataset/deletion_requests.csv output.csv")
print(f"Exit Code: {run_full_res.returncode}")
if run_full_res.stdout:
    print("STDOUT: " + run_full_res.stdout.strip())
if run_full_res.stderr:
    print("STDERR: " + run_full_res.stderr.strip())

# Compare isolated generated output.csv with scratch/candidate_output.csv
with open(full_out, 'rb') as f1, open('scratch/candidate_output.csv', 'rb') as f2:
    fout_data = f1.read()
    cand_data = f2.read()
    fout_hash = hashlib.sha256(fout_data).hexdigest()
    cand_hash = hashlib.sha256(cand_data).hexdigest()
    fout_match = (fout_data == cand_data)
    print(f"\nGenerated full output.csv: {len(fout_data):,} bytes, SHA-256: {fout_hash}")
    print(f"Candidate output.csv:      {len(cand_data):,} bytes, SHA-256: {cand_hash}")
    print(f"Bit-for-bit identical: {fout_match}")
    if not fout_match:
        print("ERROR: Generated output.csv does not match candidate_output.csv!")
        sys.exit(1)

print("\nALL CODE PACKAGE VALIDATION STEPS PASSED SUCCESSFULLY.")
