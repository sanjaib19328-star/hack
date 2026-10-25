import hashlib
import os

files = [
    'output.csv',
    'code.zip',
    'log.txt',
    'scratch/candidate_code.zip',
    'scratch/candidate_sample_pred.csv',
    'scratch/candidate_output.csv'
]

print("BASELINE CHECKSUMS (SHA-256):")
for f in files:
    if os.path.exists(f):
        h = hashlib.sha256()
        with open(f, 'rb') as fp:
            while chunk := fp.read(65536):
                h.update(chunk)
        size = os.path.getsize(f)
        print(f"  {f:<35} | size: {size:<7} bytes | sha256: {h.hexdigest()}")
    else:
        print(f"  {f:<35} | MISSING!")
