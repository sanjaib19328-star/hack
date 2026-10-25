import os
import shutil
import zipfile
import hashlib

staging_root = r'scratch\stage3_14\staged_deliverables'
agent_trace_temp = r'scratch\stage3_14\agent_trace_staging'

os.makedirs(staging_root, exist_ok=True)
if os.path.exists(agent_trace_temp):
    shutil.rmtree(agent_trace_temp)
os.makedirs(agent_trace_temp, exist_ok=True)

print("=== STEP 4: PREPARING SEPARATE CANDIDATE DELIVERABLES ===\n")

# 1. output.csv
src_output = 'scratch/candidate_output.csv'
dst_output = os.path.join(staging_root, 'output.csv')
shutil.copyfile(src_output, dst_output)
output_sha = hashlib.sha256(open(dst_output, 'rb').read()).hexdigest()
print(f"Staged output.csv: {os.path.getsize(dst_output):,} bytes, SHA-256: {output_sha}")

# 2. code.zip
src_code = 'scratch/stage3_7/patched_code.zip'
dst_code = os.path.join(staging_root, 'code.zip')
shutil.copyfile(src_code, dst_code)
code_sha = hashlib.sha256(open(dst_code, 'rb').read()).hexdigest()
print(f"Staged code.zip: {os.path.getsize(dst_code):,} bytes, SHA-256: {code_sha}")

# 3. log.txt
src_log = 'scratch/stage3_13/authentic_candidate_log.txt'
dst_log = os.path.join(staging_root, 'log.txt')
shutil.copyfile(src_log, dst_log)
log_sha = hashlib.sha256(open(dst_log, 'rb').read()).hexdigest()
print(f"Staged log.txt: {os.path.getsize(dst_log):,} bytes, SHA-256: {log_sha}")

# 4. agent-trace.zip
conv_id = '11b80a86-3ebc-4897-b88e-aa6808b8fdb9'
brain_src = rf'C:\Users\HP\.gemini\antigravity-ide\brain\{conv_id}'
antigravity_dest = os.path.join(agent_trace_temp, 'agent-trace', 'antigravity', conv_id)

print(f"\nStaging Antigravity trace from {brain_src} to {antigravity_dest}...")
shutil.copytree(brain_src, antigravity_dest)

dst_trace_zip = os.path.join(staging_root, 'agent-trace.zip')
if os.path.exists(dst_trace_zip):
    os.remove(dst_trace_zip)

print(f"Compressing {os.path.join(agent_trace_temp, 'agent-trace')} into {dst_trace_zip}...")
agent_trace_folder = os.path.join(agent_trace_temp, 'agent-trace')

with zipfile.ZipFile(dst_trace_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(agent_trace_folder):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, agent_trace_temp)
            z.write(full_path, rel_path)

trace_zip_size = os.path.getsize(dst_trace_zip)
trace_zip_sha = hashlib.sha256(open(dst_trace_zip, 'rb').read()).hexdigest()
print(f"Created agent-trace.zip: {trace_zip_size:,} bytes ({trace_zip_size / (1024*1024):.2f} MB), SHA-256: {trace_zip_sha}")

# Clean up temp uncompressed staging folder
shutil.rmtree(agent_trace_temp, ignore_errors=True)
print("Cleaned up temporary uncompressed agent_trace_staging folder.")

print("\nALL FOUR SEPARATE CANDIDATE DELIVERABLES STAGED SUCCESSFULLY.")
