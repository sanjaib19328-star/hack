import os
import zipfile
import hashlib
import csv
import json
import re
import sys

staging_dir = r'scratch\stage3_14\staged_deliverables'

print("=== STEP 5: VALIDATE EVERY STAGED CANDIDATE ===\n")

# Check 1: File existence, sizes, hashes
expected_files = ['output.csv', 'code.zip', 'log.txt', 'agent-trace.zip']
deliverable_stats = {}

for fname in expected_files:
    fpath = os.path.join(staging_dir, fname)
    if not os.path.exists(fpath):
        print(f"ERROR: Missing deliverable: {fname}")
        sys.exit(1)
    data = open(fpath, 'rb').read()
    h = hashlib.sha256(data).hexdigest()
    size = len(data)
    deliverable_stats[fname] = {'path': fpath, 'size': size, 'sha256': h}
    print(f"File: {fname}")
    print(f"  Path: {fpath}")
    print(f"  Size: {size:,} bytes")
    print(f"  SHA-256: {h}\n")

# Check 2: Validate output.csv
csv_path = deliverable_stats['output.csv']['path']
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

assert header == ['case_id', 'deletion_status', 'steps_json'], f"Header mismatch: {header}"
assert len(rows) == 518, f"Row count mismatch: {len(rows)}"
expected_cases = [f"case_{i:02d}" if i < 100 else f"case_{i}" for i in range(33, 551)]
actual_cases = [r[0] for r in rows]
assert actual_cases == expected_cases, "Case ID sequence mismatch"

for idx, (cid, status, steps_raw) in enumerate(rows, 1):
    assert status in ('COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE'), f"Invalid status: {status}"
    steps = json.loads(steps_raw)
    assert isinstance(steps, list), "steps_json is not list"
    if status == 'NOT_APPLICABLE':
        assert len(steps) == 0, f"NOT_APPLICABLE with non-empty steps: {cid}"
    else:
        assert len(steps) > 0, f"Applicable case with empty steps: {cid}"
print("output.csv: 100% compliant (518 rows, correct header, valid JSON arrays, valid statuses).")

# Check 3: Validate code.zip
zip_code_path = deliverable_stats['code.zip']['path']
expected_code_members = {
    'code/main.py',
    'code/evaluation/main.py',
    'code/evaluation/evaluation_report.md',
    'code/evaluation/usage_report.md',
    'code/evaluation/test_core_engine.py',
    'README.md'
}
with zipfile.ZipFile(zip_code_path, 'r') as z:
    code_members = set(z.namelist())
    assert code_members == expected_code_members, f"code.zip members mismatch: {code_members ^ expected_code_members}"
    # Verify main.py matches patched_main.py
    main_data = z.read('code/main.py')
    patched_data = open('scratch/stage3_7/patched_main.py', 'rb').read()
    assert main_data == patched_data, "code/main.py inside code.zip does not match patched_main.py"
print("code.zip: 100% compliant (exactly the 6 required files, zero caches, byte-for-byte main.py match).")

# Check 4: Validate log.txt
log_path = deliverable_stats['log.txt']['path']
log_content = open(log_path, 'r', encoding='utf-8').read()
blocks = log_content.split('## [')
session_starts = [b for b in blocks[1:] if 'SESSION START' in b]
turn_blocks = [b for b in blocks[1:] if 'SESSION START' not in b]
assert len(session_starts) == 1, f"Expected 1 SESSION START, got {len(session_starts)}"
assert len(turn_blocks) == 17, f"Expected 17 completed user turns, got {len(turn_blocks)}"
for idx, b in enumerate(turn_blocks, 1):
    assert 'User Prompt (verbatim, secrets redacted):' in b, f"Turn {idx} missing prompt header"
    assert 'Agent Response Summary:' in b, f"Turn {idx} missing summary header"
    assert 'Actions:' in b, f"Turn {idx} missing actions header"
    assert 'Context:' in b, f"Turn {idx} missing context header"
    assert 'tool=antigravity-ide' in b, f"Turn {idx} missing tool name"
    assert 'model=gemini-3.8-flash' in b, f"Turn {idx} missing model name"
print("log.txt: 100% compliant (Session Start + 17 turns with verbatim prompts and verified tool/model headers).")

# Check 5: Validate agent-trace.zip
trace_zip_path = deliverable_stats['agent-trace.zip']['path']
with zipfile.ZipFile(trace_zip_path, 'r') as z:
    trace_members = z.namelist()
    print(f"agent-trace.zip: Total archive members = {len(trace_members)}")
    # Verify top-level prefix is agent-trace/antigravity/
    for m in trace_members:
        assert m.startswith('agent-trace/antigravity/11b80a86-3ebc-4897-b88e-aa6808b8fdb9/'), f"Unexpected member in trace zip: {m}"
    # Verify transcript.jsonl is present
    expected_transcript = 'agent-trace/antigravity/11b80a86-3ebc-4897-b88e-aa6808b8fdb9/.system_generated/logs/transcript.jsonl'
    assert expected_transcript in trace_members, f"Missing transcript.jsonl in agent-trace.zip"
print("agent-trace.zip: 100% compliant (clean structure under agent-trace/antigravity/<conv_id>/).")

print("\nALL FOUR CANDIDATE DELIVERABLES PASSED ALL VALIDATION CHECKS.")
