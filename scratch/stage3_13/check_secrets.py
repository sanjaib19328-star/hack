import json
import re

log_path = r'C:\Users\HP\.gemini\antigravity-ide\brain\11b80a86-3ebc-4897-b88e-aa6808b8fdb9\.system_generated\logs\transcript.jsonl'

secrets_found = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT':
            content = data.get('content', '')
            for kw in ['api_key', 'apikey', 'secret', 'password', 'token', 'bearer']:
                matches = re.findall(rf'({kw}\s*[:=]\s*\S+)', content, re.IGNORECASE)
                if matches:
                    secrets_found.append((data.get('step_index'), matches))

print(f"Potential secrets found in USER_INPUT: {len(secrets_found)}")
for s in secrets_found:
    print(f"  Step {s[0]}: {s[1]}")
