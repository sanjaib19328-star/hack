import csv, json, os

manifest = {}
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        manifest[r["file_id"]] = r

# Load predictions
with open("scratch/sample_pred.csv", "r", encoding="utf-8") as f:
    preds = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

total_steps = 0
steps_with_ev = 0
valid_ev_id = 0
resource_found_in_ev = 0
unmatched_details = []

for cid, (status, steps) in preds.items():
    for s in steps:
        total_steps += 1
        ev_id = s.get("evidence_id")
        res_id = s.get("resource_id")
        phase = s.get("phase")
        if ev_id:
            steps_with_ev += 1
            if ev_id in manifest:
                valid_ev_id += 1
                ev_info = manifest[ev_id]
                fpath = os.path.join("dataset", ev_info["file_path"])
                if os.path.exists(fpath):
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                        if res_id in content:
                            resource_found_in_ev += 1
                        else:
                            unmatched_details.append((cid, res_id, ev_id, ev_info["file_path"], phase))

print(f"Total steps audited: {total_steps}")
print(f"Steps with evidence_id: {steps_with_ev}")
print(f"Evidence IDs in manifest: {valid_ev_id}/{steps_with_ev}")
print(f"Resource directly found in cited evidence file: {resource_found_in_ev}/{steps_with_ev}")
if unmatched_details:
    print(f"Unmatched details ({len(unmatched_details)}):")
    for u in unmatched_details:
        print(f"  Case: {u[0]}, Res: {u[1]}, Ev: {u[2]}, File: {u[3]}, Phase: {u[4]}")
