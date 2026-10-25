import json

log_path = r'C:\Users\HP\.gemini\antigravity-ide\brain\11b80a86-3ebc-4897-b88e-aa6808b8fdb9\.system_generated\logs\transcript.jsonl'

with open(log_path, 'r', encoding='utf-8') as f:
    for i in range(10):
        line = f.readline()
        if not line:
            break
        data = json.loads(line)
        print(f"--- Line {i} ---")
        print(f"Keys: {list(data.keys())}")
        print(f"type: {data.get('type')}, source: {data.get('source')}, status: {data.get('status')}")
        if 'tool_calls' in data:
            print(f"tool_calls count: {len(data['tool_calls'])}")
            if data['tool_calls']:
                print(f"first tool call: {data['tool_calls'][0].get('name') or data['tool_calls'][0].get('tool')}")
