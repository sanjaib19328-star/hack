import json
import re

log_path = r'C:\Users\HP\.gemini\antigravity-ide\brain\11b80a86-3ebc-4897-b88e-aa6808b8fdb9\.system_generated\logs\transcript.jsonl'

user_turns = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line_idx, line in enumerate(f):
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT':
            user_turns.append({
                'line_idx': line_idx,
                'step_index': data.get('step_index'),
                'created_at': data.get('created_at'),
                'content': data.get('content', '')
            })

print(f"Total user turns: {len(user_turns)}")
for i, ut in enumerate(user_turns, start=1):
    raw_content = ut['content']
    # extract title or first non-empty line
    clean_lines = [l.strip() for l in raw_content.splitlines() if l.strip() and not l.startswith('<USER_REQUEST>') and not l.startswith('</USER_REQUEST>')]
    title = clean_lines[0] if clean_lines else "Untitled"
    print(f"Turn {i}: Step {ut['step_index']}, Time: {ut['created_at']}")
    print(f"  Title/First line: {title[:90]}")
    print(f"  Raw prompt length: {len(raw_content)} chars")
