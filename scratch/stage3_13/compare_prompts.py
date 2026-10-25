import json
import re

# Load candidate_final_log.txt blocks
candidate_path = 'scratch/stage3_9/candidate_final_log.txt'
with open(candidate_path, 'r', encoding='utf-8') as f:
    cand_text = f.read()

cand_blocks = cand_text.split('## [')
cand_turns = []
for b in cand_blocks[1:]:
    header = b.split('\n', 1)[0]
    if 'SESSION START' in header:
        continue
    user_prompt_match = re.search(r'User Prompt \(verbatim, secrets redacted\):\s*\n(.*?)(?=\nAgent Response Summary:)', b, re.DOTALL)
    prompt = user_prompt_match.group(1).strip() if user_prompt_match else ""
    cand_turns.append((header, prompt))

# Load transcript.jsonl user inputs
log_path = r'C:\Users\HP\.gemini\antigravity-ide\brain\11b80a86-3ebc-4897-b88e-aa6808b8fdb9\.system_generated\logs\transcript.jsonl'
real_turns = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT':
            raw = data.get('content', '')
            # strip <USER_REQUEST> tags
            clean = re.sub(r'</?USER_REQUEST>', '', raw).strip()
            real_turns.append((data.get('step_index'), data.get('created_at'), clean))

print(f"Candidate turns: {len(cand_turns)}")
print(f"Real turns: {len(real_turns)}")

print("\n--- COMPARISON OF PROMPT LENGTHS ---")
for i in range(min(len(cand_turns), len(real_turns))):
    c_hdr, c_prompt = cand_turns[i]
    r_step, r_time, r_prompt = real_turns[i]
    match = (c_prompt == r_prompt)
    print(f"Turn {i+1}:")
    print(f"  Candidate header: {c_hdr[:50]}")
    print(f"  Candidate prompt len: {len(c_prompt)} chars")
    print(f"  Authentic prompt len: {len(r_prompt)} chars")
    print(f"  Exact string match: {match}")
    if not match:
        print(f"  Candidate first 60 chars: {c_prompt[:60].replace(chr(10), ' ')}")
        print(f"  Authentic first 60 chars: {r_prompt[:60].replace(chr(10), ' ')}")
