import csv, json, os

sample_cases = ["case_01", "case_05", "case_06", "case_07", "case_08"]

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("scratch/candidate_sample_pred.csv", "r", encoding="utf-8") as f:
    preds = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    ev_manifest = {r["file_id"]: r for r in csv.DictReader(f)}

with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    identities = {r["user_id"]: r for r in csv.DictReader(f)}
email_to_uid = {r["email"].lower(): r["user_id"] for r in identities.values()}

for cid in sample_cases:
    req = reqs[cid]
    status, steps = preds[cid]
    email = req["email"].lower().strip()
    user_id = email_to_uid.get(email, "UNKNOWN")
    print(f"\n=======================================================")
    print(f"CASE: {cid} | Status: {status} | Steps Count: {len(steps)} | User: {user_id}")
    for s in steps:
        step_no = s["step_no"]
        phase = s["phase"]
        sys_id = s["system_id"]
        res_id = s["resource_id"]
        op = s["operation"]
        st = s["state"]
        ev_id = s["evidence_id"]
        print(f"  Step {step_no} [{phase}]: {sys_id} -> {res_id} | Op: {op} | State: {st} | Ev: '{ev_id}'")
        if ev_id:
            ev_meta = ev_manifest[ev_id]
            ev_path = os.path.join("dataset", ev_meta["file_path"])
            with open(ev_path, "r", encoding="utf-8", errors="ignore") as fp:
                c = fp.read()
            has_u = user_id in c or email in c.lower()
            has_r = res_id in c
            print(f"    Ev File: {ev_meta['file_path']} | User in content? {has_u} | Res in content? {has_r}")
