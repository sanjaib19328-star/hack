import os
import re
import json

base_dir = r'C:\Users\HP\.gemini\antigravity-ide\brain\11b80a86-3ebc-4897-b88e-aa6808b8fdb9'

# Regex patterns for various secrets and sensitive tokens
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?', "API Key"),
    (r'(?i)(bearer\s+[a-zA-Z0-9_\-\.]{20,})', "Bearer Token"),
    (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?', "Password"),
    (r'AIzaSy[a-zA-Z0-9_\-]{33}', "Google API Key"),
    (r'sk-[a-zA-Z0-9]{32,}', "OpenAI API Key"),
    (r'sk-ant-[a-zA-Z0-9_\-]{32,}', "Anthropic API Key"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
    (r'gho_[a-zA-Z0-9]{36}', "GitHub OAuth Token"),
    (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "Private Key Header"),
    (r'(?i)(session[_-]?token|access[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?', "Access/Session Token"),
]

print("=== STARTING COMPREHENSIVE PRIVACY & SECRET AUDIT ===\n")

total_files_scanned = 0
total_bytes_scanned = 0
findings = []

for root, dirs, files in os.walk(base_dir):
    for f in files:
        fp = os.path.join(root, f)
        rel_p = os.path.relpath(fp, base_dir)
        total_files_scanned += 1
        size = os.path.getsize(fp)
        total_bytes_scanned += size
        
        # Check binary images
        if f.endswith('.png') or f.endswith('.jpg') or f.endswith('.jpeg'):
            # Binary check for strings or headers
            data = open(fp, 'rb').read()
            # Verify PNG header
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                findings.append((rel_p, "Invalid PNG header or corrupted file", "Warning"))
            continue
            
        # Text/JSON/JSONL/Python files
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as file_obj:
                content = file_obj.read()
                
            for pattern, p_name in SECRET_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    # Filter out benign mock/fictional keys from problem statement or tests
                    filtered_matches = []
                    for m in matches:
                        m_str = str(m)
                        if 'sk-...' in m_str or 'AIzaSy...' in m_str or 'REDACTED' in m_str or 'example' in m_str.lower():
                            continue
                        filtered_matches.append(p_name)
                    if filtered_matches:
                        findings.append((rel_p, f"Potential {p_name} ({len(filtered_matches)} instances)", "Alert"))
        except Exception as e:
            findings.append((rel_p, f"Error reading file: {e}", "Error"))

print(f"Total files audited: {total_files_scanned}")
print(f"Total volume audited: {total_bytes_scanned:,} bytes ({total_bytes_scanned / (1024*1024):.2f} MB)")
print(f"\nAudit findings count: {len(findings)}")

if findings:
    print("Findings breakdown:")
    for fpath, desc, level in findings:
        print(f"  [{level}] {fpath}: {desc}")
else:
    print("\nPRIVACY & SECRET AUDIT PASSED: ZERO secrets, tokens, private keys, or passwords detected.")
