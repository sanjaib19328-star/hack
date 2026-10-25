import re

def audit_candidate_log():
    text = open('scratch/stage3_9/candidate_final_log.txt', 'r', encoding='utf-8', errors='replace').read()
    blocks = text.split('## [')

    print(f"Total blocks separated by ## [: {len(blocks) - 1}")

    for idx, b in enumerate(blocks[1:], 1):
        header_line = b.split('\n', 1)[0]
        print(f"--- Block {idx}: ## [{header_line} ---")
        if 'SESSION START' in header_line:
            # Check session start fields
            for field in ['tool=', 'model=', 'Repo Root:', 'Branch:', 'Worktree:', 'Parent Agent:', 'Language:', 'Time Remaining:']:
                matching = [line for line in b.splitlines() if line.startswith(field)]
                if matching:
                    print(f"  {matching[0]}")
                else:
                    print(f"  MISSING FIELD: {field}")
        else:
            has_user_prompt = 'User Prompt (verbatim, secrets redacted):' in b
            has_summary = 'Agent Response Summary:' in b
            has_actions = 'Actions:' in b
            has_context = 'Context:' in b
            tools = re.findall(r'^tool=(.+)', b, re.MULTILINE)
            models = re.findall(r'^model=(.+)', b, re.MULTILINE)
            
            missing = []
            if not has_user_prompt: missing.append('User Prompt')
            if not has_summary: missing.append('Agent Response Summary')
            if not has_actions: missing.append('Actions')
            if not has_context: missing.append('Context')
            if not tools: missing.append('tool=')
            if not models: missing.append('model=')
            
            summary_match = re.search(r'Agent Response Summary:\s*\n(.*?)(?=\n\s*Actions:)', b, re.DOTALL)
            sentence_count = 0
            if summary_match:
                summary_text = summary_match.group(1).strip()
                sentences = [s for s in re.split(r'\. |\.\n', summary_text) if s.strip()]
                sentence_count = len(sentences)
                
            print(f"  Missing fields: {missing if missing else 'None'}")
            print(f"  tool: {tools[0] if tools else 'NONE'}, model: {models[0] if models else 'NONE'}")
            print(f"  Summary sentence count: {sentence_count}")

if __name__ == '__main__':
    audit_candidate_log()
