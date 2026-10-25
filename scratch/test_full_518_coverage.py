import csv, json, os, re

reqs = list(csv.DictReader(open("dataset/deletion_requests.csv", encoding="utf-8")))

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    ev_files = list(csv.DictReader(f))

# Let's map trace_to_user in logs
user_to_acc = {}
user_to_aud = {}

for ev in ev_files:
    fpath = os.path.join("dataset", ev["file_path"])
    if not os.path.exists(fpath): continue
    if fpath.endswith(".log"):
        with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
            lines = fp.readlines()
        
        trace_map = {}
        for l in lines:
            m_tr = re.search(r"(?:trace_id|requestId)=([^\s,\"]+)", l)
            if not m_tr: continue
            tr = m_tr.group(1)
            m_usr = re.search(r"(?:lookup_key|subject_key|subject_ref|match_key|owner_key)=\"?([^\s\",]+)\"?", l)
            if m_usr:
                trace_map[tr] = m_usr.group(1)
                
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

# Also load from system_activity
act_acc = {}
act_aud = {}
with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        res = r.get("resource_id")
        target = r.get("target_system")
        details = r.get("details", "")
        m_u = re.search(r"user_\d+", details)
        m_e = re.search(r"[\w\.-]+@[\w\.-]+", details)
        if target == "account_service" and res and res.startswith("account_"):
            if m_u: act_acc[m_u.group(0)] = res
            if m_e: act_acc[m_e.group(0).lower()] = res
        if target == "security_service" and res and res.startswith("audit_record_"):
            if m_u: act_aud[m_u.group(0)] = res
            if m_e: act_aud[m_e.group(0).lower()] = res

# Also load from json evidence files directly
ev_acc = {}
ev_aud = {}
for ev in ev_files:
    fpath = os.path.join("dataset", ev["file_path"])
    if not os.path.exists(fpath): continue
    if fpath.endswith(".json"):
        try:
            with open(fpath, "r", encoding="utf-8") as fp:
                d = json.load(fp)
            if "snapshots" in d:
                for s in d["snapshots"]:
                    for rec in s.get("records", []):
                        res = rec.get("resource_id")
                        e = (rec.get("email") or "").lower()
                        u = rec.get("customer_reference") or rec.get("subject_reference") or rec.get("user_id")
                        if s.get("data_store") == "account_service" and res and res.startswith("account_"):
                            if e: ev_acc[e] = res
                            if u: ev_acc[str(u)] = res
                        if s.get("data_store") == "security_service" and res and res.startswith("audit_record_"):
                            if e: ev_aud[e] = res
                            if u: ev_aud[str(u)] = res
        except Exception:
            pass

# Also load from sql dumps
sql_acc = {}
for ev in ev_files:
    fpath = os.path.join("dataset", ev["file_path"])
    if not os.path.exists(fpath): continue
    if fpath.endswith(".sql"):
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                for line in fp:
                    m_a = re.search(r"(account_\d+)", line)
                    m_e = re.search(r"[\w\.-]+@[\w\.-]+", line)
                    if m_a and m_e:
                        sql_acc[m_e.group(0).lower()] = m_a.group(1)
        except Exception:
            pass

missing_acc = 0
found_acc = 0
for r in reqs:
    e = r["email"].lower()
    acc = user_to_acc.get(e) or act_acc.get(e) or ev_acc.get(e) or sql_acc.get(e)
    if not acc:
        missing_acc += 1
    else:
        found_acc += 1

print(f"Total requests in full dataset: {len(reqs)}")
print(f"Found grounded account: {found_acc}/{len(reqs)}")
print(f"Missing account: {missing_acc}/{len(reqs)}")
