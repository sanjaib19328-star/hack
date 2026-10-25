import os
import zipfile
import hashlib

output_zip_path = 'scratch/stage3_12/Ghost_Data_Still_Exists_Submission.zip'

source_files = {
    'output.csv': ('scratch/candidate_output.csv', '43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd'),
    'code.zip': ('scratch/stage3_7/patched_code.zip', '63b2ed2175aa89b6443ff616198b3910cdb8d2fd380f915890005a6e7e1fb818'),
    'log.txt': ('scratch/stage3_9/candidate_final_log.txt', 'ce32768808fbcec57458570f5cf62dc714c11c06932307db0d6ac42bfcf3a56a')
}

print(f"Creating submission zip: {output_zip_path}...")

# Create ZIP
with zipfile.ZipFile(output_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for arcname, (src_path, expected_hash) in source_files.items():
        data = open(src_path, 'rb').read()
        actual_hash = hashlib.sha256(data).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {src_path}!"
        z.writestr(arcname, data)
        print(f"  Added {arcname} from {src_path} ({len(data):,} bytes)")

zip_size = os.path.getsize(output_zip_path)
zip_hash = hashlib.sha256(open(output_zip_path, 'rb').read()).hexdigest()

print(f"\nSubmission ZIP successfully created.")
print(f"File Path: {output_zip_path}")
print(f"Size: {zip_size:,} bytes ({zip_size / (1024*1024):.3f} MB)")
print(f"SHA-256: {zip_hash}")
print(f"Under 50 MB limit: {zip_size < 50 * 1024 * 1024}")

# Verify archive reading and member checksums
print("\nVerifying archive members:")
with zipfile.ZipFile(output_zip_path, 'r') as z:
    for info in z.infolist():
        content = z.read(info.filename)
        h = hashlib.sha256(content).hexdigest()
        expected = source_files[info.filename][1]
        print(f"  {info.filename}: {info.file_size:,} bytes (compressed: {info.compress_size:,}), SHA-256: {h}")
        assert h == expected, f"Verification failed for {info.filename}!"

print("\nALL SUBMISSION ZIP INTEGRITY CHECKS PASSED.")
