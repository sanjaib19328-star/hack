import json

log_path = r'C:\Users\HP\.gemini\antigravity-ide\brain\11b80a86-3ebc-4897-b88e-aa6808b8fdb9\.system_generated\logs\transcript.jsonl'

lines = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        lines.append(json.loads(line))

print(f"Total lines in transcript.jsonl: {len(lines)}")

user_input_indices = [i for i, d in enumerate(lines) if d.get('type') == 'USER_INPUT']
print(f"User input indices: {user_input_indices}")

for turn_idx, start_idx in enumerate(user_input_indices):
    end_idx = user_input_indices[turn_idx + 1] if turn_idx + 1 < len(user_input_indices) else len(lines)
    turn_steps = lines[start_idx:end_idx]
    
    # User input
    u_step = turn_steps[0]
    u_content = u_step.get('content', '')
    clean_lines = [l.strip() for l in u_content.splitlines() if l.strip() and not l.startswith('<USER_REQUEST>') and not l.startswith('</USER_REQUEST>')]
    title = clean_lines[0] if clean_lines else "Untitled"
    
    # Collect tools called during this turn
    tools_called = set()
    for s in turn_steps:
        tc = s.get('tool_calls', [])
        for call in tc:
            tname = call.get('name') or call.get('tool')
            if tname:
                tools_called.add(tname)
                
    # Find final planner response (the message delivered to the user)
    planner_responses = [s for s in turn_steps if s.get('type') == 'PLANNER_RESPONSE' and s.get('content')]
    final_resp = planner_responses[-1].get('content', '') if planner_responses else ""
    first_few_resp = final_resp.strip()[:150].replace('\n', ' ')
    
    print(f"\nTurn {turn_idx + 1}: {title[:60]}")
    print(f"  Time: {u_step.get('created_at')}")
    print(f"  Step span: {start_idx} to {end_idx - 1} ({len(turn_steps)} events)")
    print(f"  Tools called: {sorted(list(tools_called))}")
    print(f"  Final response preview: {first_few_resp}...")
