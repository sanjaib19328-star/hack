import zipfile, os

zip_path = "scratch/candidate_code.zip"
if os.path.exists(zip_path):
    os.remove(zip_path)

files_to_include = [
    ("code/main.py", "code/main.py"),
    ("code/evaluation/main.py", "code/evaluation/main.py"),
    ("code/evaluation/evaluation_report.md", "code/evaluation/evaluation_report.md"),
    ("code/evaluation/usage_report.md", "code/evaluation/usage_report.md"),
    ("code/evaluation/test_core_engine.py", "code/evaluation/test_core_engine.py"),
    ("README.md", "README.md")
]

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for src, arc in files_to_include:
        z.write(src, arc)

print(f"Created {zip_path}")
print("Candidate ZIP contents:")
with zipfile.ZipFile(zip_path, "r") as z:
    for info in z.infolist():
        print(f"  {info.filename} ({info.file_size} bytes, compressed to {info.compress_size} bytes)")
