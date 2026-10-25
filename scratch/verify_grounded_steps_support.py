import csv
import json
import os

print("=== Task 3: Verifying Account-Grounding Correction in Candidate Deliverables ===")

target_10 = ["case_09", "case_18", "case_20", "case_22", "case_23", "case_25", "case_28", "case_29", "case_31", "case_32"]

with open("scratch/candidate_sample_pred.csv", "r", encoding="utf-8") as f:
    sample_rows = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

print("\n1. Checking the 10 ambiguous cases in candidate_sample_pred.csv:")
speculative_emitted = []
for cid in target_10:
    stat, steps = sample_rows[cid]
    acc_steps = [s for s in steps if s["system_id"] == "account_service"]
    print(f"  {cid} ({stat}): total steps = {len(steps)} | account_service steps = {[s['resource_id'] for s in acc_steps]}")
    if acc_steps:
        speculative_emitted.append((cid, acc_steps))

if not speculative_emitted:
    print("  -> CONFIRMED: Engine emits ZERO speculative account IDs for all 10 ambiguous cases!")
else:
    print(f"  -> FAILED: Speculative account IDs found: {speculative_emitted}")

print("\n2. Checking all remaining account_service steps in candidate_sample_pred.csv:")
# For every case that has account_service step, check its evidence support
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    ev_files = {r["file_id"]: r for r in csv.DictReader(f)}

with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    identities = {r["user_id"]: r for r in csv.DictReader(f)}
email_to_uid = {r["email"].lower(): r["user_id"] for r in identities.values()}

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    reqs = {r["case_id"]: r for r in csv.DictReader(f)}

account_verified_cases = []
for cid, (stat, steps) in sample_rows.items():
    acc_steps = [s for s in steps if s["system_id"] == "account_service"]
    if acc_steps:
        req = reqs[cid]
        email = req["email"].lower().strip()
        uid = email_to_uid.get(email)
        for s in acc_steps:
            ev_id = s.get("evidence_id")
            ev_path = ev_files.get(ev_id, {}).get("file_path", "N/A")
            account_verified_cases.append((cid, uid, s["resource_id"], s["operation"], s["state"], ev_id, ev_path))

print(f"Total remaining account_service steps across 32 sample cases: {len(account_verified_cases)}")
for c in account_verified_cases:
    uid_str = str(c[1]) if c[1] is not None else "None"
    print(f"  Case: {c[0]:<8} | User: {uid_str:<8} | Res: {c[2]:<14} | Op: {c[3]:<22} | Ev: {c[5]} ({c[6]})")
