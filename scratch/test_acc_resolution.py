import os, csv, re, json

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    ev_files = list(csv.DictReader(f))

# Let's map trace_to_user in logs
log_trace_to_user = {}
user_to_acc = {}
user_to_aud = {}

for ev in ev_files:
    fpath = os.path.join("dataset", ev["file_path"])
    if not os.path.exists(fpath): continue
    if fpath.endswith(".log"):
        with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
            lines = fp.readlines()
        
        # 1. First pass: find trace to user
        trace_map = {}
        for l in lines:
            m_tr = re.search(r"(?:trace_id|requestId)=([^\s,\"]+)", l)
            if not m_tr: continue
            tr = m_tr.group(1)
            m_usr = re.search(r"(?:lookup_key|subject_key|subject_ref|match_key|owner_key)=\"?([^\s\",]+)\"?", l)
            if m_usr:
                trace_map[tr] = m_usr.group(1)
                
        # 2. Second pass: find resource_id associated with trace
        for l in lines:
            m_tr = re.search(r"(?:trace_id|requestId)=([^\s,\"]+)", l)
            if not m_tr: continue
            tr = m_tr.group(1)
            usr = trace_map.get(tr)
            if not usr: continue
            
            m_acc = re.search(r"resource_id=(account_\d+)", l)
            if m_acc:
                user_to_acc[usr.lower()] = m_acc.group(1)
            m_aud = re.search(r"resource_id=(audit_record_\d+)", l)
            if m_aud:
                user_to_aud[usr.lower()] = m_aud.group(1)

print(f"Discovered via trace correlation:")
print(f"  user_to_acc: {len(user_to_acc)} mappings")
print(f"  user_to_aud: {len(user_to_aud)} mappings")
for u, a in list(user_to_acc.items())[:10]:
    print(f"  {u} -> {a}")
