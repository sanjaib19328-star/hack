import json
import re

log_path = r'C:\Users\HP\.gemini\antigravity-ide\brain\11b80a86-3ebc-4897-b88e-aa6808b8fdb9\.system_generated\logs\transcript.jsonl'

lines = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        lines.append(json.loads(line))

user_indices = [i for i, d in enumerate(lines) if d.get('type') == 'USER_INPUT']

for idx, u_idx in enumerate(user_indices):
    next_u_idx = user_indices[idx + 1] if idx + 1 < len(user_indices) else len(lines)
    turn_steps = lines[u_idx:next_u_idx]
    
    # User step
    u_step = turn_steps[0]
    prompt = u_step.get('content', '')
    clean_prompt = re.sub(r'</?USER_REQUEST>', '', prompt).strip()
    first_line = [l.strip() for l in clean_prompt.splitlines() if l.strip()][0]
    
    # Response
    planner_resps = [s for s in turn_steps if s.get('type') == 'PLANNER_RESPONSE' and s.get('content')]
    final_resp = planner_resps[-1].get('content', '') if planner_resps else ""
    
    # Tools
    tools_used = []
    for s in turn_steps:
        for call in s.get('tool_calls', []):
            name = call.get('name') or call.get('tool')
            args = call.get('args', {})
            # extract key info like filename or command
            target = args.get('TargetFile') or args.get('AbsolutePath') or args.get('CommandLine') or args.get('Query')
            if target and len(str(target)) > 60:
                target = str(target)[:57] + '...'
            tools_used.append((name, target))
            
    print(f"Turn {idx+1}: {first_line[:50]}")
    print(f"  Timestamp: {u_step.get('created_at')}")
    print(f"  Total steps in turn: {len(turn_steps)}")
    print(f"  Tools called count: {len(tools_used)}")
    if tools_used:
        print(f"  First 3 tool calls: {tools_used[:3]}")
    print()
