import csv
import json
import os
import re

print("=== Investigation of the 10 Target Cases for Account Identity Grounding ===")

target_cases = ["case_09", "case_18", "case_20", "case_22", "case_23", "case_25", "case_28", "case_29", "case_31", "case_32"]

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    sample_truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    identities = {r["user_id"]: r for r in csv.DictReader(f)}
email_to_uid = {r["email"].lower(): r["user_id"] for r in identities.values()}

with open("dataset/user_audit_log.csv", "r", encoding="utf-8") as f:
    audit_logs = list(csv.DictReader(f))

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    activities = list(csv.DictReader(f))

# Check each case
for cid in target_cases:
    req = sample_reqs[cid]
    email = req["email"].lower().strip()
    user_id = email_to_uid.get(email)
    req_at = req["requested_at"]
    rep_at = req["reported_at"]
    aud_at = req["audit_at"]
    
    print(f"\n=======================================================")
    print(f"CASE: {cid} | User: {user_id} | Email: {email}")
    print(f"Window: {req_at} -> {rep_at} (Audit: {aud_at})")
    print(f"Request: {req['request_text']}")
    
    # 1. Check user_audit_log for aliases or account mentions
    u_aliases = [row for row in audit_logs if row["user_id"] == user_id]
    print(f"User Audit Log entries ({len(u_aliases)}):")
    for a in u_aliases:
        print(f"  {a['event_time']} | {a['field_name']}: {a['old_value']} -> {a['new_value']}")
        
    # 2. Check all worker activities in window
    w_acts = [
        a for a in activities
        if a["source_system"] == "deletion_worker" and 
           a["target_system"] == "account_service" and 
           req_at <= a["event_time"] <= rep_at
    ]
    print(f"Candidate deletion_worker activities in window ({len(w_acts)}):")
    for w in w_acts:
        print(f"  {w['event_time']} | {w['activity_id']} | {w['reported_result']} | {w['resource_id']} | {w['details']}")
        
    # 3. Check if any activity mentions this user or email anywhere in system_activity
    user_acts = [
        a for a in activities
        if (user_id and user_id in str(a)) or (email in str(a).lower())
    ]
    print(f"Total system_activity rows explicitly mentioning user/email: {len(user_acts)}")
    for ua in user_acts[:5]:
        print(f"  {ua['event_time']} | {ua['source_system']} -> {ua['target_system']} | {ua['resource_id']} | {ua['details']}")
        
    # 4. Check truth steps for account_service
    t_stat, t_steps = sample_truth[cid]
    t_acc = [s for s in t_steps if s["system_id"] == "account_service"]
    print(f"Truth account_service step: {t_acc}")
